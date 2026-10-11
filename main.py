"""Retired: the AI Advisor now lives on the main site, behind login.

This tiny app only exists so the old address (ai.uzonwokoro.com, and the Heroku
app URL) forwards to the new private page instead of exposing anything. Once the
`nwokoro-ai` Heroku app and its DNS record are removed, this file can be deleted.
"""
import os

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

NEW_HOME = "https://uzonwokoro.com/networth/advisor/"

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.api_route("/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
def moved(path: str):
    return RedirectResponse(NEW_HOME, status_code=301)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
