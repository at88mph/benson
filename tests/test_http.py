"""Benson HTTP tests."""

from __future__ import annotations

import os
import re
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
async def test_startsession_json_shape(client: AsyncClient) -> None:
    ep = quote_endpoint("http://registry.example/oai")
    resp = await client.get(f"/api/v1/registry-validate/harvest?endpoint={ep}&op=StartSession")
    assert resp.status_code == 200
    assert "sessionURL" in resp.text
    assert extract_run_id(resp.text)


@pytest.mark.asyncio
async def test_unknown_op_400(client: AsyncClient) -> None:
    ep = quote_endpoint("http://registry.example/oai")
    r1 = await client.get(f"/api/v1/registry-validate/harvest?endpoint={ep}&op=StartSession")
    rid = extract_run_id(r1.text)
    assert rid
    r2 = await client.get(f"/api/v1/registry-validate/harvest?runid={rid}&op=Bogus")
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_validator_form(client: AsyncClient) -> None:
    resp = await client.get("/validator")
    assert resp.status_code == 200
    assert "Registry validator" in resp.text
    assert 'name="endpoint"' in resp.text
    assert 'name="builtin_schemas"' in resp.text
    assert "Use built-in XSD schemas" in resp.text
    assert "dry run" in resp.text.lower()


@pytest.mark.asyncio
async def test_validator_rejects_empty_endpoint(client: AsyncClient) -> None:
    resp = await client.post("/validator", data={"endpoint": "   "})
    assert resp.status_code == 400
    assert "Enter an OAI-PMH endpoint URL" in resp.text


def quote_endpoint(endpoint: str) -> str:
    from urllib.parse import quote

    return quote(endpoint, safe="")


def extract_run_id(body: str) -> str | None:
    m = re.search(r"runid=([^&'\s,\}]+)", body)
    return m.group(1) if m else None
