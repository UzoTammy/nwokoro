from advisor.tools import (
    get_borrowed_funds,
    get_businesses,
    get_exchange_rates,
    get_fixed_assets,
    get_investments,
    get_liabilities,
    get_net_worth_summary,
    get_savings,
    get_stocks,
)

SYSTEM_PROMPT = """You are a sharp personal financial advisor for the Nwokoro financial dashboard.
Answer questions using the financial data provided. Be specific with numbers and percentages.
Highlight risks, opportunities, and actionable steps. Format responses in clear markdown.
Use the web_search tool when the user asks about current events, recent news, live exchange rates,
Nigerian investment climate, new regulations, or any topic requiring up-to-date information.

Response length: keep answers concise and focused by default — 3 to 6 sentences or a short
bullet list is ideal. Only expand into a detailed or lengthy response when the user explicitly
asks for it (e.g. "explain in detail", "give me a full breakdown", "elaborate")."""


def build_financial_context() -> str:
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
        lines.append(
            f"  {s['holder']} ({s['currency']}): {s['value']} — {s['category']} [{s['host_country']}]"
        )

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
                f"  {s['holder']} ({s['stock_type']}): {s['units']} units @ "
                f"{s['unit_cost']} {s['currency']} = {s['cost_value']} cost / {s['market_value']} market"
            )

    lines += ["", "=== BUSINESSES ==="]
    for b in get_businesses():
        if b["is_active"]:
            lines.append(
                f"  {b['name']}: {b['shares']} shares @ {b['unit_cost']} {b['currency']} = {b['capital']}"
            )

    lines += ["", "=== FIXED ASSETS ==="]
    for fa in get_fixed_assets():
        if fa["is_active"]:
            lines.append(f"  {fa['name']}: {fa['value']} {fa['currency']} [{fa['host_country']}]")

    lines += ["", "=== LIABILITIES ==="]
    for lb in get_liabilities():
        lines.append(
            f"  {lb['name']}: balance {lb['balance_amount']} {lb['currency']} "
            f"(initial {lb['initial_amount']}) @ {lb['interest_rate']}%"
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
