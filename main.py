import os
import sys
from decimal import Decimal
from pathlib import Path

# Bootstrap Django before any app imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nwokoro.settings")

import django
django.setup()

import json
import uvicorn
from anthropic import Anthropic
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("nwokoro", host="0.0.0.0", port=int(os.getenv("PORT", 8001)))
anthropic_client = Anthropic()


class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------

@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
def get_net_worth_summary() -> dict:
    """Calculate total net worth across all asset classes, converted to USD."""
    from datetime import datetime, timezone
    from networth.models import (
        Saving, Investment, Stock, Business, FixedAsset,
        Liability, BorrowedFund, ExchangeRate,
    )

    exchange_rates_qs = list(ExchangeRate.objects.all())
    rates = {er.target_currency: Decimal(str(er.rate)) for er in exchange_rates_qs}
    rates["USD"] = Decimal("1")

    def to_usd(amount, currency: str) -> float:
        rate = rates.get(currency, Decimal("1"))
        return float(Decimal(str(amount)) / rate)

    savings_usd = sum(to_usd(s.value.amount, s.value_currency) for s in Saving.objects.all())
    investments_usd = sum(
        to_usd(i.principal.amount, i.principal_currency)
        for i in Investment.objects.filter(is_active=True)
    )
    stocks_usd = sum(
        to_usd(s.unit_cost.amount * s.units, s.unit_cost_currency)
        for s in Stock.objects.filter(date_sold__isnull=True)
    )
    businesses_usd = sum(
        to_usd(b.unit_cost.amount * b.shares, b.unit_cost_currency)
        for b in Business.objects.filter(is_active=True)
    )
    fixed_assets_usd = sum(
        to_usd(fa.value.amount, fa.value_currency)
        for fa in FixedAsset.objects.filter(is_active=True)
    )
    liabilities_usd = sum(
        to_usd(l.balance_amount.amount, l.balance_amount_currency)
        for l in Liability.objects.all()
    )
    borrowed_usd = sum(
        to_usd(bf.settlement_amount.amount, bf.settlement_amount_currency)
        for bf in BorrowedFund.objects.filter(is_active=True)
    )

    total_assets = savings_usd + investments_usd + stocks_usd + businesses_usd + fixed_assets_usd
    total_liabilities = liabilities_usd + borrowed_usd

    oldest_rate = min((er.updated_at for er in exchange_rates_qs), default=None)
    newest_rate = max((er.updated_at for er in exchange_rates_qs), default=None)

    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "exchange_rates_last_updated": {
            "oldest": oldest_rate.isoformat() if oldest_rate else None,
            "newest": newest_rate.isoformat() if newest_rate else None,
        },
        "savings_usd": round(savings_usd, 2),
        "investments_usd": round(investments_usd, 2),
        "stocks_usd": round(stocks_usd, 2),
        "businesses_usd": round(businesses_usd, 2),
        "fixed_assets_usd": round(fixed_assets_usd, 2),
        "total_assets_usd": round(total_assets, 2),
        "liabilities_usd": round(liabilities_usd, 2),
        "borrowed_funds_usd": round(borrowed_usd, 2),
        "total_liabilities_usd": round(total_liabilities, 2),
        "net_worth_usd": round(total_assets - total_liabilities, 2),
    }


# ---------------------------------------------------------------------------
# FastAPI app — REST wrappers (visible in /docs) + MCP SSE mounted at /mcp
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Nwokoro MCP Server",
    description="Financial data API and MCP server for Nwokoro personal finance management.",
    version="1.0.0",
)


@app.get("/tools/exchange-rates", tags=["Finance"])
def api_exchange_rates():
    """Get all current exchange rates."""
    return get_exchange_rates()


@app.get("/tools/savings", tags=["Finance"])
def api_savings():
    """List all savings accounts with current balances."""
    return get_savings()


@app.get("/tools/investments", tags=["Finance"])
def api_investments():
    """List all investments (active and inactive)."""
    return get_investments()


@app.get("/tools/liabilities", tags=["Finance"])
def api_liabilities():
    """List all liabilities with outstanding balances."""
    return get_liabilities()


@app.get("/tools/borrowed-funds", tags=["Finance"])
def api_borrowed_funds():
    """List all borrowed funds (short-term liabilities)."""
    return get_borrowed_funds()


@app.get("/tools/stocks", tags=["Finance"])
def api_stocks():
    """List all stock holdings."""
    return get_stocks()


@app.get("/tools/businesses", tags=["Finance"])
def api_businesses():
    """List all business holdings."""
    return get_businesses()


@app.get("/tools/fixed-assets", tags=["Finance"])
def api_fixed_assets():
    """List all fixed assets."""
    return get_fixed_assets()


@app.get("/tools/net-worth", tags=["Finance"])
def api_net_worth():
    """Calculate total net worth in USD across all asset classes."""
    return get_net_worth_summary()


@app.get("/", include_in_schema=False)
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/advisor")


@app.get("/advisor", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    html_path = BASE_DIR / "ai" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


def _build_financial_context() -> str:
    summary = get_net_worth_summary()
    lines = [
        f"Financial snapshot as of {summary['as_of']}",
        f"Exchange rates last updated: {summary['exchange_rates_last_updated']['newest']}",
        "",
        "=== NET WORTH SUMMARY (USD) ===",
        f"  Savings:       ${summary['savings_usd']:>12,.2f}",
        f"  Investments:   ${summary['investments_usd']:>12,.2f}",
        f"  Stocks:        ${summary['stocks_usd']:>12,.2f}",
        f"  Businesses:    ${summary['businesses_usd']:>12,.2f}",
        f"  Fixed Assets:  ${summary['fixed_assets_usd']:>12,.2f}",
        f"  TOTAL ASSETS:  ${summary['total_assets_usd']:>12,.2f}",
        "",
        f"  Liabilities:   ${summary['liabilities_usd']:>12,.2f}",
        f"  Borrowed:      ${summary['borrowed_funds_usd']:>12,.2f}",
        f"  TOTAL LIAB:    ${summary['total_liabilities_usd']:>12,.2f}",
        "",
        f"  NET WORTH:     ${summary['net_worth_usd']:>12,.2f}",
        "",
        "=== SAVINGS ACCOUNTS ===",
    ]
    for s in get_savings():
        lines.append(f"  {s['holder']} ({s['currency']}): {s['value']} — {s['category']} [{s['host_country']}]")

    lines += ["", "=== ACTIVE INVESTMENTS ==="]
    for i in get_investments():
        if i["is_active"]:
            lines.append(
                f"  {i['holder']}: {i['principal']} {i['currency']} @ {i['rate']}% "
                f"for {i['duration_days']} days from {i['start_date']}"
            )

    lines += ["", "=== STOCKS (unsold) ==="]
    for s in get_stocks():
        if s["is_active"]:
            lines.append(
                f"  {s['holder']} ({s['stock_type']}): {s['units']} units @ {s['unit_cost']} {s['currency']} "
                f"= {s['cost_value']} cost / {s['market_value']} market"
            )

    lines += ["", "=== BUSINESSES ==="]
    for b in get_businesses():
        if b["is_active"]:
            lines.append(f"  {b['name']}: {b['shares']} shares @ {b['unit_cost']} {b['currency']} = {b['capital']}")

    lines += ["", "=== FIXED ASSETS ==="]
    for fa in get_fixed_assets():
        if fa["is_active"]:
            lines.append(f"  {fa['name']}: {fa['value']} {fa['currency']} [{fa['host_country']}]")

    lines += ["", "=== LIABILITIES ==="]
    for l in get_liabilities():
        lines.append(
            f"  {l['name']}: balance {l['balance_amount']} {l['currency']} "
            f"(initial {l['initial_amount']}) @ {l['interest_rate']}%"
        )

    lines += ["", "=== BORROWED FUNDS ==="]
    for bf in get_borrowed_funds():
        if bf["is_active"]:
            lines.append(
                f"  {bf['source']}: borrowed {bf['borrowed_amount']} {bf['currency']}, "
                f"settlement {bf['settlement_amount']}, due {bf['terminal_date']}"
            )

    lines += ["", "=== EXCHANGE RATES ==="]
    for er in get_exchange_rates():
        lines.append(f"  1 {er['base']} = {er['rate']} {er['target']} (updated {er['updated_at']})")

    return "\n".join(lines)


SYSTEM_PROMPT = """You are a sharp personal financial advisor for the Nwokoro financial dashboard.
Answer questions using the financial data provided. Be specific with numbers and percentages.
Highlight risks, opportunities, and actionable steps. Format responses in clear markdown."""


@app.post("/chat", tags=["AI"])
def chat(body: ChatRequest):
    context = _build_financial_context()
    system = f"{SYSTEM_PROMPT}\n\n{context}"
    messages = body.history + [{"role": "user", "content": body.question}]

    def generate():
        with anthropic_client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield f"data: {json.dumps(text)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# MCP SSE protocol — mount last so FastAPI routes take precedence
app.mount("/mcp", mcp.sse_app(mount_path="/mcp"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
