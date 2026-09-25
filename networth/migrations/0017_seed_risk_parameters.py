from decimal import Decimal

from django.db import migrations

INITIAL = 'Initial estimate (Sep 2026) - review and cite a source'

COUNTRIES = [
    # code, sovereign, convertibility
    ('WORLD', 0.0, 0.0),
    ('CA', 0.0, 0.0),
    ('US', 0.0, 0.0),
    ('NG', 0.04, 0.05),
]

CURRENCIES = [
    # currency, stress_floor (1-year bad-year loss vs USD)
    ('USD', 0.0),
    ('CAD', 0.10),
    ('NGN', 0.40),
]

INSTITUTIONS = [
    # name, aliases, failure_probability, loss_given_failure, insured_limit, source
    ('Scotia Bank', 'Scotia Inv Cash', 0.002, 0.5, (Decimal('100000'), 'CAD'), 'CDIC C$100k cover; systemically important bank'),
    ('RBC Bank', '', 0.002, 0.5, (Decimal('100000'), 'CAD'), 'CDIC C$100k cover; systemically important bank'),
    ('UBA', '', 0.03, 0.6, (Decimal('5000000'), 'NGN'), 'NDIC cover - verify current limit; tier-1 NG bank'),
    ('Axa Mansard', 'Axa Mansard MM, Axa Mansard USD', 0.02, 0.3, None, 'Asset manager; client assets held in separate custody'),
    ('OminiPay', '', 0.05, 0.7, None, 'Fintech; no deposit insurance assumed'),
]

ASSET_TYPES = [
    # asset_class, category, stress
    ('saving', '', 0.0),
    ('investment', '', 0.0),
    ('investment', 'CP', 0.05),
    ('stock', '', 0.40),
    ('stock', 'Scotia Essential', 0.15),
    ('stock', 'Scotia Selected', 0.18),
    ('business', '', 0.50),
    ('fixed_asset', '', 0.15),
]


def seed(apps, schema_editor):
    CountryRisk = apps.get_model('networth', 'CountryRisk')
    CurrencyRisk = apps.get_model('networth', 'CurrencyRisk')
    InstitutionRisk = apps.get_model('networth', 'InstitutionRisk')
    AssetTypeRisk = apps.get_model('networth', 'AssetTypeRisk')

    for code, sovereign, convertibility in COUNTRIES:
        CountryRisk.objects.get_or_create(code=code, defaults={
            'sovereign': sovereign, 'convertibility': convertibility, 'source': INITIAL})

    for currency, floor in CURRENCIES:
        CurrencyRisk.objects.get_or_create(currency=currency, defaults={'stress_floor': floor, 'source': INITIAL})

    for name, aliases, pd, lgd, limit, source in INSTITUTIONS:
        defaults = {'aliases': aliases, 'failure_probability': pd, 'loss_given_failure': lgd,
                    'source': f'{INITIAL}. {source}'}
        if limit:
            defaults['insured_limit'], defaults['insured_limit_currency'] = limit
        InstitutionRisk.objects.get_or_create(name=name, defaults=defaults)

    for asset_class, category, stress in ASSET_TYPES:
        AssetTypeRisk.objects.get_or_create(asset_class=asset_class, category=category, defaults={
            'stress': stress, 'source': INITIAL})


def unseed(apps, schema_editor):
    for model in ('CountryRisk', 'CurrencyRisk', 'InstitutionRisk', 'AssetTypeRisk'):
        apps.get_model('networth', model).objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('networth', '0016_risk_parameters'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
