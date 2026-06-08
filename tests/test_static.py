"""Static assets and templates."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
import httpx

_repo = Path(__file__).resolve().parents[1]
os.environ.setdefault("SCHEMA_ROOT", str(_repo / "assets" / "schemas"))
os.environ.setdefault("ASSETS_ROOT", str(_repo / "assets" / "validate"))

from benson.app import create_app, fastapi_app  # noqa: E402
from benson.config import Settings  # noqa: E402


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    settings = Settings.from_env()
    app = create_app()
    core = fastapi_app(app)
    async with httpx.AsyncClient() as hc:
        core.state.settings = settings
        core.state.http_client = hc
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_static_css(client: AsyncClient) -> None:
    resp = await client.get("/static/css/ivoa-theme.css")
    assert resp.status_code == 200
    assert "--ivoa-primary:" in resp.text
    assert "--accent:" in resp.text

    common = await client.get("/static/css/common.css")
    assert common.status_code == 200


@pytest.mark.asyncio
async def test_pages_load_ivoa_theme(client: AsyncClient) -> None:
    for path in ("/", "/validator"):
        resp = await client.get(path)
        assert resp.status_code == 200
        assert "fonts.googleapis.com" in resp.text
        assert "ivoa-theme.css" in resp.text
        assert "Inter" in resp.text


@pytest.mark.asyncio
async def test_url_for_uses_forwarded_proto(client: AsyncClient) -> None:
    resp = await client.get(
        "/validator",
        headers={
            "X-Forwarded-Proto": "https",
            "X-Forwarded-Host": "rofr.example.org",
        },
    )
    assert resp.status_code == 200
    assert "https://rofr.example.org/static/css/validator.css" in resp.text


@pytest.mark.asyncio
async def test_static_validator_js(client: AsyncClient) -> None:
    resp = await client.get("/static/js/validator-watch.js")
    assert resp.status_code == 200
    assert "/validator/jobs" in resp.text
