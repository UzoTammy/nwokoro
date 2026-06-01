import json
import os
import sys
from pathlib import Path

# Bootstrap Django before any app imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nwokoro.settings")

import django
django.setup()

import uvicorn
from anthropic import Anthropic
from django.conf import settings as django_settings
from django.core.mail import EmailMessage
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from advisor.tools import (
    SEARCH_TOOL,
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
    register_tools,
    tavily_search,
)

# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------

mcp = FastMCP("nwokoro", host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
register_tools(mcp)

anthropic_client = Anthropic()


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    history: list[dict] = []


class ShareRequest(BaseModel):
    content_html: str
    title: str = "Financial Advisor Note"


class TitleRequest(BaseModel):
    title: str


class MessageRequest(BaseModel):
    role: str
    content: str


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Nwokoro AI Advisor",
    description="Financial data API, AI advisor, and MCP server for Nwokoro personal finance.",
    version="1.0.0",
)

# ── REST wrappers (visible in /docs) ────────────────────────────────────────

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


@app.get("/tools/networth-history", tags=["Insights"])
def api_networth_history(months: int = 6):
    """Daily net worth snapshots for the past N months."""
    return get_networth_history(months)


@app.get("/tools/recent-transactions", tags=["Insights"])
def api_recent_transactions(days: int = 30):
    """All transactions across every asset class for the past N days."""
    return get_recent_transactions(days)


@app.get("/tools/maturing-investments", tags=["Insights"])
def api_maturing_investments(days: int = 60):
    """Active investments maturing within the next N days."""
    return get_maturing_investments(days)


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/advisor")


@app.get("/advisor", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    html_path = BASE_DIR / "ai" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/capabilities", response_class=HTMLResponse, include_in_schema=False)
def capabilities():
    html_path = BASE_DIR / "ai" / "capabilities.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


# ── AI chat ──────────────────────────────────────────────────────────────────

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
                f"  {s['holder']} ({s['stock_type']}): {s['units']} units @ "
                f"{s['unit_cost']} {s['currency']} = {s['cost_value']} cost / {s['market_value']} market"
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
Highlight risks, opportunities, and actionable steps. Format responses in clear markdown.
Use the web_search tool when the user asks about current events, recent news, live exchange rates,
Nigerian investment climate, new regulations, or any topic requiring up-to-date information.

Response length: keep answers concise and focused by default — 3 to 6 sentences or a short
bullet list is ideal. Only expand into a detailed or lengthy response when the user explicitly
asks for it (e.g. "explain in detail", "give me a full breakdown", "elaborate")."""


@app.post("/chat", tags=["AI"])
def chat(body: ChatRequest):
    """Stream an AI advisor response, using web search when current data is needed."""
    context  = _build_financial_context()
    system   = f"{SYSTEM_PROMPT}\n\n{context}"
    messages = body.history + [{"role": "user", "content": body.question}]

    def generate():
        current_messages = list(messages)
        tools_used       = False

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=current_messages,
            tools=[SEARCH_TOOL],
        )

        while response.stop_reason == "tool_use":
            tools_used   = True
            tool_results = []
            for block in response.content:
                if block.type == "tool_use" and block.name == "web_search":
                    query = block.input.get("query", "")
                    yield f"data: {json.dumps(chr(10) + '🔍 *Searching: ' + query + '…*' + chr(10) + chr(10))}\n\n"
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     tavily_search(query),
                    })

            current_messages = current_messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user",      "content": tool_results},
            ]
            response = anthropic_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=system,
                messages=current_messages,
                tools=[SEARCH_TOOL],
            )

        if tools_used:
            with anthropic_client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=system,
                messages=current_messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps(text)}\n\n"
        else:
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    text = block.text
                    for i in range(0, len(text), 80):
                        yield f"data: {json.dumps(text[i:i + 80])}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Share (email / PDF) ───────────────────────────────────────────────────────

def _wrap_html_for_export(body_html: str, title: str) -> str:
    from datetime import datetime
    timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: "Segoe UI", Arial, sans-serif; max-width: 740px; margin: 40px auto; color: #0f172a; line-height: 1.7; }}
    header {{ background: linear-gradient(140deg,#0f172a,#1e293b,#334155); color:#f8fafc; border-radius: 12px; padding: 28px 32px; margin-bottom: 32px; }}
    header h1 {{ margin: 0 0 6px; font-size: 1.3rem; }}
    header p  {{ margin: 0; font-size: 0.82rem; color: #94a3b8; }}
    .content {{ padding: 0 4px; }}
    h1,h2,h3 {{ color: #1e293b; }}
    code {{ background:#f1f5f9; border:1px solid #dbe3ee; padding:0.1em 0.35em; border-radius:4px; font-size:0.88em; }}
    pre  {{ background:#f1f5f9; border:1px solid #dbe3ee; padding:1rem; border-radius:8px; overflow:auto; }}
    table {{ width:100%; border-collapse:collapse; margin:1rem 0; }}
    th,td {{ border:1px solid #dbe3ee; padding:8px 12px; text-align:left; }}
    th {{ background:#f8fafc; font-weight:700; }}
    footer {{ margin-top:40px; padding-top:16px; border-top:1px solid #dbe3ee; font-size:0.78rem; color:#94a3b8; text-align:center; }}
  </style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <p>Nwokoro Financial Advisor &bull; {timestamp}</p>
  </header>
  <div class="content">{body_html}</div>
  <footer>Generated by Nwokoro AI Advisor &mdash; ai.uzonwokoro.com/advisor</footer>
</body>
</html>"""


@app.post("/share/email", tags=["AI"])
def share_email(body: ShareRequest):
    """Email an advisor response to the owner."""
    from networth.models import User
    owner = User.objects.filter(is_superuser=True).first() or User.objects.first()
    if not owner:
        return {"status": "error", "message": "No owner account found."}

    html = _wrap_html_for_export(body.content_html, body.title)
    msg  = EmailMessage(
        subject=f"Advisor Note — {body.title}",
        body=html,
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        to=[owner.email],
    )
    msg.content_subtype = "html"
    msg.send()
    return {"status": "success", "message": f"Sent to {owner.email}"}


@app.post("/share/pdf", tags=["AI"])
def share_pdf(body: ShareRequest):
    """Return an advisor response as a downloadable PDF."""
    from weasyprint import HTML
    html      = _wrap_html_for_export(body.content_html, body.title)
    pdf_bytes = HTML(string=html, base_url="").write_pdf()
    safe      = body.title.encode("ascii", "ignore").decode("ascii")
    filename  = (safe.replace(" ", "_").strip("_")[:40] or "advisor_note") + ".pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Conversation store ───────────────────────────────────────────────────────

@app.get("/convs/", tags=["Conversations"])
def list_convs():
    """List all conversations ordered by most recently updated."""
    from advisor.models import Conversation
    return [
        {"id": c.id, "title": c.title, "updated_at": c.updated_at.isoformat()}
        for c in Conversation.objects.all()
    ]


@app.post("/convs/", tags=["Conversations"])
def create_conv():
    """Create a new conversation and return its id and title."""
    from advisor.models import Conversation
    conv = Conversation.objects.create()
    return {"id": conv.id, "title": conv.title}


@app.delete("/convs/{conv_id}", tags=["Conversations"])
def delete_conv(conv_id: int):
    """Delete a conversation and all its messages."""
    from advisor.models import Conversation
    deleted, _ = Conversation.objects.filter(pk=conv_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}


@app.patch("/convs/{conv_id}/title", tags=["Conversations"])
def rename_conv(conv_id: int, body: TitleRequest):
    """Set the title of a conversation (called after the first message)."""
    from advisor.models import Conversation
    updated = Conversation.objects.filter(pk=conv_id).update(title=body.title[:120])
    if not updated:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "ok"}


@app.get("/convs/{conv_id}/messages/", tags=["Conversations"])
def get_messages(conv_id: int):
    """Return all messages for a conversation as a history array."""
    from advisor.models import Conversation, Message
    if not Conversation.objects.filter(pk=conv_id).exists():
        raise HTTPException(status_code=404, detail="Conversation not found")
    return [
        {"role": m.role, "content": m.content}
        for m in Message.objects.filter(conversation_id=conv_id)
    ]


@app.post("/convs/{conv_id}/messages/", tags=["Conversations"])
def append_message(conv_id: int, body: MessageRequest):
    """Append a message to a conversation and touch its updated_at timestamp."""
    from advisor.models import Conversation, Message
    from django.utils import timezone
    try:
        conv = Conversation.objects.get(pk=conv_id)
    except Conversation.DoesNotExist:
        raise HTTPException(status_code=404, detail="Conversation not found")
    Message.objects.create(conversation=conv, role=body.role, content=body.content)
    conv.updated_at = timezone.now()
    conv.save(update_fields=["updated_at"])
    return {"status": "ok"}


# ── MCP SSE — mount last so FastAPI routes take precedence ───────────────────

app.mount("/mcp", mcp.sse_app(mount_path="/mcp"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
