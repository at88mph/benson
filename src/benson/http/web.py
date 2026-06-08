"""Jinja templates and static file mounting."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from benson.config import Settings


def configure_web(app: FastAPI, settings: Settings) -> Jinja2Templates:
    templates = Jinja2Templates(directory=str(settings.templates_dir))
    app.state.templates = templates
    if not any(getattr(r, "name", None) == "static" for r in app.routes):
        app.mount(
            "/static",
            StaticFiles(directory=str(settings.static_dir)),
            name="static",
        )
    return templates
