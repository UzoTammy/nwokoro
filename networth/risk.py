"""
Portfolio risk score: the fraction of the USD value of all assets that could be
lost in a 1-in-20 bad year (0-1). Methodology: networth/learn/risk-score/.

Each asset passes through four layers that compound on the value left after
the layer before it:

    asset_risk = 1 - (1 - world)(1 - country)(1 - institution)(1 - asset_type)

country itself compounds sovereign, currency (by the asset's currency, not
its host country) and convertibility stress. The portfolio score is the
USD-value-weighted average of asset_risk.
"""
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .models import (
    Saving, Investment, Stock, Business, FixedAsset, ExchangeRate,
    CountryRisk, CurrencyRisk, InstitutionRisk, AssetTypeRisk,
)
from .tools import _fit_fx_process

# Fallbacks for anything without a parameter row - deliberately cautious, and
# always reported as unrated so the gap gets filled in admin.
DEFAULT_SOVEREIGN = 0.10
DEFAULT_CURRENCY_FLOOR = 0.25
DEFAULT_FAILURE_PROBABILITY = 0.05
DEFAULT_LOSS_GIVEN_FAILURE = 0.7
DEFAULT_ASSET_STRESS = 0.25

Z_95 = 1.645  # one-sided 95th percentile of the normal distribution
LAYERS = ('world', 'country', 'institution', 'asset_type')
BANDS = [(0.10, 'Low', 'success'), (0.25, 'Moderate', 'info'), (0.50, 'High', 'warning'), (1.01, 'Severe', 'danger')]


@dataclass
class AssetRisk:
    name: str
    asset_class: str
    category: str
    country: str
    currency: str
    holder: Optional[str]
    value_usd: float
    layers: dict = field(default_factory=dict)
    points: float = 0.0  # contribution to the portfolio score, in percentage points

    @property
    def risk(self):
        remaining = 1.0
        for layer in LAYERS:
            remaining *= 1 - self.layers.get(layer, 0.0)
        return 1 - remaining

    @property
    def layers_pct(self):
        return {layer: value * 100 for layer, value in self.layers.items()}


def currency_stress(owner, currency: str, floor: float) -> tuple[float, Optional[float]]:
    """
    1-year, 95th-percentile loss of `currency` against USD. Uses the higher of
    the long-run floor and the figure fitted from the app's own FX snapshots,
    because the stored history is too short and calm to see a 1-in-20 year.
    """
    if currency == 'USD':
        return 0.0, None
    fx = _fit_fx_process(owner, currency, window_days=365)
    computed = None
    if fx is not None:
        # rates are units per USD, so a rising rate is a USD loss
        q = fx['mu_daily'] * 365 + Z_95 * fx['sigma_daily'] * np.sqrt(365)
        computed = max(0.0, float(1 - np.exp(-q)))
    return max(floor, computed or 0.0), computed


def _active_assets(owner):
    for s in Saving.objects.filter(owner=owner, value__gt=0):
        yield AssetRisk(f'{s.holder} {s.category}', 'saving', s.category, s.host_country,
                        str(s.value_currency), s.holder, float(s.to_usd().amount))
    for i in Investment.objects.filter(owner=owner, is_active=True):
        yield AssetRisk(f'{i.holder} {i.category}', 'investment', i.category, i.host_country,
                        str(i.principal_currency), i.holder, float(i.to_usd().amount))
    # stocks, businesses and property carry their issuer risk in the asset-type
    # layer; there is no deposit-taking institution to fail, so holder=None
    for s in Stock.objects.filter(owner=owner, units__gt=0):
        yield AssetRisk(f'{s.holder} {s.stock_type}', 'stock', s.stock_type, s.host_country,
                        str(s.unit_cost_currency), None, float(s.to_usd().amount))
    for b in Business.objects.filter(owner=owner, is_active=True):
        yield AssetRisk(b.name, 'business', '', b.host_country,
                        str(b.unit_cost_currency), None, float(b.to_usd().amount))
    for f in FixedAsset.objects.filter(owner=owner, is_active=True):
        yield AssetRisk(f.name, 'fixed_asset', '', f.host_country,
                        str(f.value_currency), None, float(f.to_usd().amount))


def portfolio_risk(owner) -> dict:
    assets = [a for a in _active_assets(owner) if a.value_usd > 0]
    total = sum(a.value_usd for a in assets)
    if not total:
        return {'available': False}

    countries = {c.code: c for c in CountryRisk.objects.all()}
    currencies = {c.currency: c for c in CurrencyRisk.objects.all()}
    asset_types = {(t.asset_class, t.category): t for t in AssetTypeRisk.objects.all()}
    institutions = list(InstitutionRisk.objects.all())
    by_name = {n: inst for inst in institutions for n in inst.names()}
    rates = dict(ExchangeRate.objects.values_list('target_currency', 'rate'))
    params = [*countries.values(), *currencies.values(), *asset_types.values(), *institutions]
    unrated = set()

    world = countries.get(CountryRisk.WORLD)
    world_stress = world.stress() if world else 0.0

    currency_cache = {}
    for code in {a.currency for a in assets}:
        row = currencies.get(code)
        if row is None and code != 'USD':
            unrated.add(f'currency {code}')
        currency_cache[code] = currency_stress(owner, code, row.stress_floor if row else DEFAULT_CURRENCY_FLOOR)

    # deposit insurance applies to everything held at one institution combined
    holder_totals = {}
    for a in assets:
        if a.holder:
            inst = by_name.get(a.holder.lower())
            key = inst.name if inst else a.holder
            holder_totals[key] = holder_totals.get(key, 0.0) + a.value_usd

    for a in assets:
        a.layers['world'] = world_stress

        country = countries.get(a.country)
        if country is None:
            unrated.add(f'country {a.country}')
        if country and country.at_war:
            country_stress = 1.0
        else:
            sovereign = country.sovereign if country else DEFAULT_SOVEREIGN
            convertibility = country.convertibility if country else 0.0
            country_stress = 1 - (1 - sovereign) * (1 - currency_cache[a.currency][0]) * (1 - convertibility)
        a.layers['country'] = country_stress

        if a.holder:
            inst = by_name.get(a.holder.lower())
            if inst is None:
                unrated.add(f'institution {a.holder}')
            pd = inst.failure_probability if inst else DEFAULT_FAILURE_PROBABILITY
            lgd = inst.loss_given_failure if inst else DEFAULT_LOSS_GIVEN_FAILURE
            uninsured = 1.0
            if inst and inst.insured_limit and inst.insured_limit.amount and rates.get(str(inst.insured_limit.currency)):
                limit_usd = float(inst.insured_limit.amount) / rates[str(inst.insured_limit.currency)]
                uninsured = max(0.0, 1 - limit_usd / holder_totals[inst.name])
            a.layers['institution'] = pd * lgd * uninsured
        else:
            a.layers['institution'] = 0.0

        asset_type = asset_types.get((a.asset_class, a.category)) or asset_types.get((a.asset_class, ''))
        if asset_type is None:
            unrated.add(f'asset type {a.asset_class}')
        a.layers['asset_type'] = asset_type.stress if asset_type else DEFAULT_ASSET_STRESS

    # attribute each asset's loss to layers in order, so the parts sum to the score
    layer_totals = dict.fromkeys(LAYERS, 0.0)
    for a in assets:
        weight, remaining = a.value_usd / total, 1.0
        for layer in LAYERS:
            loss = remaining * a.layers[layer]
            layer_totals[layer] += weight * loss
            remaining -= loss

    for a in assets:
        a.points = a.value_usd * a.risk / total * 100
    score = sum(a.value_usd * a.risk for a in assets) / total
    band, band_class = next((label, css) for limit, label, css in BANDS if score < limit)
    top = sorted(assets, key=lambda a: a.value_usd * a.risk, reverse=True)[:3]

    return {
        'available': True,
        'score': score,
        'score_pct': score * 100,
        'band': band,
        'band_class': band_class,
        'layers_pct': {layer: value * 100 for layer, value in layer_totals.items()},
        'top': [{'name': a.name, 'risk_pct': a.risk * 100, 'points': a.points} for a in top],
        'currency_stress_pct': {code: s * 100 for code, (s, _) in currency_cache.items()},
        'unrated': sorted(unrated),
        'stale_count': sum(1 for p in params if p.is_stale),
        'total_usd': total,
        'assets': assets,
    }
