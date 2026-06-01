import os
from decimal import Decimal

# ---------------------------------------------------------------------------
# Web search configuration
# ---------------------------------------------------------------------------

FINANCE_DOMAINS = [
    # Nigeria — regulatory & market
    "cbn.gov.ng", "sec.gov.ng", "ngxgroup.com", "fmf.gov.ng",
    # Nigeria — financial news & research
    "businessday.ng", "nairametrics.com", "prosharenigeria.com",
    "thisdaylive.com", "vanguardngr.com",
    # Canada — regulatory & market
    "bankofcanada.ca", "osc.ca", "csa-acvm.ca", "tmx.com",
    # Canada — financial news
    "financialpost.com", "bnnbloomberg.ca", "theglobeandmail.com",
    # Global authorities relevant to both
    "reuters.com", "ft.com", "bloomberg.com", "imf.org", "worldbank.org",
]

SEARCH_TOOL = {
    "name": "web_search",
    "description": (
        "Search the web for current information — Nigerian investment climate, exchange rates, "
        "CBN policies, SEC regulations, Canadian market news, or any topic requiring up-to-date "
        "financial information."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search query"}
        },
        "required": ["query"],
    },
}


def tavily_search(query: str) -> str:
    """Execute a finance-scoped web search via Tavily and return formatted results."""
    from tavily import TavilyClient
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))
    data = client.search(
        query=query,
        max_results=5,
        topic="finance",
        include_domains=FINANCE_DOMAINS,
    )
    results = []
    for r in data.get("results", []):
        results.append(f"**{r['title']}**\n{r['content']}\nSource: {r['url']}")
    return "\n\n---\n\n".join(results) if results else "No results found."


# ---------------------------------------------------------------------------
# Financial data tools
# ---------------------------------------------------------------------------

def get_exchange_rates() -> list[dict]:
    """Return all current exchange rates stored in the database."""
    from networth.models import ExchangeRate
    return [
        {
            "base": er.base_currency,
            "target": er.target_currency,
            "rate": er.rate,
            "updated_at": er.updated_at.isoformat(),
        }
        for er in ExchangeRate.objects.all()
    ]


def get_savings() -> list[dict]:
    """Return all savings accounts with current balances."""
    from networth.models import Saving
    return [
        {
            "owner": s.owner.email,
            "holder": s.holder,
            "value": str(s.value.amount),
            "currency": s.value_currency,
            "host_country": s.host_country,
            "category": s.category,
            "description": s.description,
        }
        for s in Saving.objects.select_related("owner").all()
    ]


def get_investments() -> list[dict]:
    """Return all investments (active and inactive)."""
    from networth.models import Investment
    return [
        {
            "owner": inv.owner.email,
            "holder": inv.holder,
            "principal": str(inv.principal.amount),
            "currency": inv.principal_currency,
            "rate": inv.rate,
            "start_date": inv.start_date.isoformat(),
            "duration_days": inv.duration,
            "host_country": inv.host_country,
            "category": inv.category,
            "is_active": inv.is_active,
        }
        for inv in Investment.objects.select_related("owner").all()
    ]


def get_liabilities() -> list[dict]:
    """Return all liabilities with outstanding balances."""
    from networth.models import Liability
    return [
        {
            "owner": l.owner.email,
            "name": l.name,
            "initial_amount": str(l.initial_amount.amount),
            "balance_amount": str(l.balance_amount.amount),
            "currency": l.balance_amount_currency,
            "interest_rate": float(l.interest),
            "pay_method": l.pay_method,
            "host_country": l.host_country,
            "date": l.date.isoformat() if l.date else None,
        }
        for l in Liability.objects.select_related("owner").all()
    ]


def get_borrowed_funds() -> list[dict]:
    """Return all borrowed funds (short-term liabilities)."""
    from networth.models import BorrowedFund
    return [
        {
            "owner": bf.owner.email,
            "source": bf.source,
            "borrowed_amount": str(bf.borrowed_amount.amount),
            "settlement_amount": str(bf.settlement_amount.amount),
            "currency": bf.borrowed_amount_currency,
            "date": bf.date.isoformat() if bf.date else None,
            "terminal_date": bf.terminal_date.isoformat() if bf.terminal_date else None,
            "is_active": bf.is_active,
            "description": bf.description,
        }
        for bf in BorrowedFund.objects.select_related("owner").all()
    ]


def get_stocks() -> list[dict]:
    """Return all stock holdings. Active stocks have no date_sold."""
    from networth.models import Stock
    return [
        {
            "owner": s.owner.email,
            "holder": s.holder,
            "units": s.units,
            "unit_cost": str(s.unit_cost.amount),
            "unit_price": str(s.unit_price.amount),
            "currency": s.unit_cost_currency,
            "cost_value": str((s.unit_cost * s.units).amount),
            "market_value": str((s.unit_price * s.units).amount),
            "host_country": s.host_country,
            "stock_type": s.stock_type,
            "date_bought": s.date_bought.isoformat() if s.date_bought else None,
            "date_sold": s.date_sold.isoformat() if s.date_sold else None,
            "is_active": s.date_sold is None,
        }
        for s in Stock.objects.select_related("owner").all()
    ]


def get_businesses() -> list[dict]:
    """Return all business holdings with capital value."""
    from networth.models import Business
    return [
        {
            "owner": b.owner.email,
            "name": b.name,
            "shares": b.shares,
            "unit_cost": str(b.unit_cost.amount),
            "capital": str((b.unit_cost * b.shares).amount),
            "currency": b.unit_cost_currency,
            "host_country": b.host_country,
            "date": b.date.isoformat() if b.date else None,
            "is_active": b.is_active,
            "description": b.description,
        }
        for b in Business.objects.select_related("owner").all()
    ]


def get_fixed_assets() -> list[dict]:
    """Return all fixed assets (property, equipment, etc.)."""
    from networth.models import FixedAsset
    return [
        {
            "owner": fa.owner.email,
            "name": fa.name,
            "value": str(fa.value.amount),
            "currency": fa.value_currency,
            "host_country": fa.host_country,
            "date": fa.date.isoformat() if fa.date else None,
            "growth_rate": fa.growth_rate,
            "is_active": fa.is_active,
            "description": fa.description,
        }
        for fa in FixedAsset.objects.select_related("owner").all()
    ]


def get_net_worth_summary() -> dict:
    """Calculate total net worth across all asset classes, converted to USD."""
    from datetime import datetime, timezone
    from networth.models import (
        BorrowedFund, Business, ExchangeRate,
        FixedAsset, Investment, Liability, Saving, Stock,
    )

    exchange_rates_qs = list(ExchangeRate.objects.all())
    rates = {er.target_currency: Decimal(str(er.rate)) for er in exchange_rates_qs}
    rates["USD"] = Decimal("1")

    def to_usd(amount, currency: str) -> float:
        rate = rates.get(currency, Decimal("1"))
        return float(Decimal(str(amount)) / rate)

    savings_usd      = sum(to_usd(s.value.amount, s.value_currency) for s in Saving.objects.all())
    investments_usd  = sum(to_usd(i.principal.amount, i.principal_currency) for i in Investment.objects.filter(is_active=True))
    stocks_usd       = sum(to_usd(s.unit_cost.amount * s.units, s.unit_cost_currency) for s in Stock.objects.filter(date_sold__isnull=True))
    businesses_usd   = sum(to_usd(b.unit_cost.amount * b.shares, b.unit_cost_currency) for b in Business.objects.filter(is_active=True))
    fixed_assets_usd = sum(to_usd(fa.value.amount, fa.value_currency) for fa in FixedAsset.objects.filter(is_active=True))
    liabilities_usd  = sum(to_usd(l.balance_amount.amount, l.balance_amount_currency) for l in Liability.objects.all())
    borrowed_usd     = sum(to_usd(bf.settlement_amount.amount, bf.settlement_amount_currency) for bf in BorrowedFund.objects.filter(is_active=True))

    total_assets      = savings_usd + investments_usd + stocks_usd + businesses_usd + fixed_assets_usd
    total_liabilities = liabilities_usd + borrowed_usd
    oldest_rate       = min((er.updated_at for er in exchange_rates_qs), default=None)
    newest_rate       = max((er.updated_at for er in exchange_rates_qs), default=None)

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "exchange_rates_last_updated": {
            "oldest": oldest_rate.isoformat() if oldest_rate else None,
            "newest": newest_rate.isoformat() if newest_rate else None,
        },
        "savings_usd":          round(savings_usd, 2),
        "investments_usd":      round(investments_usd, 2),
        "stocks_usd":           round(stocks_usd, 2),
        "businesses_usd":       round(businesses_usd, 2),
        "fixed_assets_usd":     round(fixed_assets_usd, 2),
        "total_assets_usd":     round(total_assets, 2),
        "liabilities_usd":      round(liabilities_usd, 2),
        "borrowed_funds_usd":   round(borrowed_usd, 2),
        "total_liabilities_usd": round(total_liabilities, 2),
        "net_worth_usd":        round(total_assets - total_liabilities, 2),
    }


# ---------------------------------------------------------------------------
# MCP registration
# ---------------------------------------------------------------------------

_FINANCIAL_TOOLS = (
    get_exchange_rates,
    get_savings,
    get_investments,
    get_liabilities,
    get_borrowed_funds,
    get_stocks,
    get_businesses,
    get_fixed_assets,
    get_net_worth_summary,
)


def register_tools(mcp) -> None:
    """Register all financial tools with the given FastMCP instance."""
    for fn in _FINANCIAL_TOOLS:
        mcp.tool()(fn)
