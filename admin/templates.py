"""Template rendering for custom admin pages (shares sqladmin's engine)."""

from typing import Any

from starlette.templating import Jinja2Templates
from starlette.requests import Request

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def render(request: Request, name: str, ctx: dict[str, Any]):
    return _templates.TemplateResponse(request, name, ctx)
