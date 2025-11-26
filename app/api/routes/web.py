"""
Web Routes

Serves HTML templates for the web dashboard.
"""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

# Templates directory
templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render the main dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """Render the search page."""
    return templates.TemplateResponse("search.html", {"request": request})


@router.get("/lenders", response_class=HTMLResponse)
async def lenders_page(request: Request):
    """Render the lenders list page."""
    return templates.TemplateResponse("lenders.html", {"request": request})


@router.get("/products", response_class=HTMLResponse)
async def products_page(request: Request):
    """Render the products list page."""
    return templates.TemplateResponse("products.html", {"request": request})


@router.get("/changes", response_class=HTMLResponse)
async def changes_page(request: Request):
    """Render the changes/history page."""
    return templates.TemplateResponse("changes.html", {"request": request})
