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
from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from advisor.routes import chat, conversations, finance, pages, share
from advisor.tools import register_tools

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Advisor",
    description="Financial data API, AI advisor, and MCP server for Nwokoro personal finance.",
    version="1.0.0",
)

app.include_router(pages.router)
app.include_router(finance.router)
app.include_router(chat.router)
app.include_router(share.router)
app.include_router(conversations.router)

# ---------------------------------------------------------------------------
# MCP server — mounted last so FastAPI routes take precedence
# ---------------------------------------------------------------------------

mcp = FastMCP("nwokoro", host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
register_tools(mcp)
app.mount("/mcp", mcp.sse_app(mount_path="/mcp"))

# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
