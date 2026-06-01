from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, RedirectResponse

router = APIRouter()

_TEMPLATES = Path(__file__).resolve().parents[1] / "templates"


@router.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/advisor")


@router.get("/advisor", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    return HTMLResponse(content=(_TEMPLATES / "index.html").read_text(encoding="utf-8"))


@router.get("/capabilities", response_class=HTMLResponse, include_in_schema=False)
def capabilities():
    return HTMLResponse(content=(_TEMPLATES / "capabilities.html").read_text(encoding="utf-8"))
