from fastapi import APIRouter

from advisor.tools import (
    get_borrowed_funds,
    get_businesses,
    get_exchange_rates,
    get_fixed_assets,
    get_investments,
    get_liabilities,
    get_maturing_investments,
    get_net_worth_summary,
    get_networth_history,
    get_recent_transactions,
    get_savings,
    get_stocks,
)

router = APIRouter(prefix="/tools", tags=["Finance"])


@router.get("/exchange-rates")
def api_exchange_rates():
    """Get all current exchange rates."""
    return get_exchange_rates()


@router.get("/savings")
def api_savings():
    """List all savings accounts with current balances."""
    return get_savings()


@router.get("/investments")
def api_investments():
    """List all investments (active and inactive)."""
    return get_investments()


@router.get("/liabilities")
def api_liabilities():
    """List all liabilities with outstanding balances."""
    return get_liabilities()


@router.get("/borrowed-funds")
def api_borrowed_funds():
    """List all borrowed funds (short-term liabilities)."""
    return get_borrowed_funds()


@router.get("/stocks")
def api_stocks():
    """List all stock holdings."""
    return get_stocks()


@router.get("/businesses")
def api_businesses():
    """List all business holdings."""
    return get_businesses()


@router.get("/fixed-assets")
def api_fixed_assets():
    """List all fixed assets."""
    return get_fixed_assets()


@router.get("/net-worth")
def api_net_worth():
    """Calculate total net worth in USD across all asset classes."""
    return get_net_worth_summary()


@router.get("/networth-history", tags=["Insights"])
def api_networth_history(months: int = 6):
    """Daily net worth snapshots for the past N months."""
    return get_networth_history(months)


@router.get("/recent-transactions", tags=["Insights"])
def api_recent_transactions(days: int = 30):
    """All transactions across every asset class for the past N days."""
    return get_recent_transactions(days)


@router.get("/maturing-investments", tags=["Insights"])
def api_maturing_investments(days: int = 60):
    """Active investments maturing within the next N days."""
    return get_maturing_investments(days)
