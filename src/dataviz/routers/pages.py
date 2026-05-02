"""HTML page routes using Jinja2 templates."""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from dataviz.logger import get_logger

logger = get_logger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))



@router.get("/")
async def index(request: Request):
    """Serve the main application page."""
    return templates.TemplateResponse(request=request, name="index.html")
