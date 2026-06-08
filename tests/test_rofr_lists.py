"""Unit tests for RofR list parsers and landing page."""

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
from benson.service.rofr_lists import (  # noqa: E402
    SearchableRegistry,
    parse_publishers_oai,
)


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


_MIN_PUBLISHERS = b"""<?xml version="1.0" encoding="UTF-8"?>
<oai:OAI-PMH xmlns:oai="http://www.openarchives.org/OAI/2.0/">
<oai:ListRecords>
<oai:record>
  <oai:header><oai:identifier>ivo://example/reg</oai:identifier></oai:header>
  <oai:metadata>
    <ri:Resource xmlns:ri="http://www.ivoa.net/xml/RegistryInterface/v1.0"
                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:vg="http://www.ivoa.net/xml/VORegistry/v1.0"
                 xsi:type="vg:Registry">
      <title>Example Registry</title>
      <capability standardID="ivo://ivoa.net/std/registry" xsi:type="vg:Harvest">
        <interface xsi:type="vg:OAIHTTP">
          <accessURL>https://registry.example/oai</accessURL>
        </interface>
      </capability>
    </ri:Resource>
  </oai:metadata>
</oai:record>
</oai:ListRecords>
</oai:OAI-PMH>
"""


def test_parse_publishers_oai_finds_harvest_url() -> None:
    rows = parse_publishers_oai(_MIN_PUBLISHERS)
    assert len(rows) == 1
    r = rows[0]
    assert r.oai_identifier == "ivo://example/reg"
    assert r.title == "Example Registry"
    assert r.harvest_access_url == "https://registry.example/oai"


@pytest.mark.asyncio
async def test_home_page_renders_with_mocked_lists(
    monkeypatch: pytest.MonkeyPatch, client: AsyncClient
) -> None:
    import benson.http.home as home

    async def _fake_load(*_a, **_k):
        return [
            SearchableRegistry(
                title="Example VO",
                href="https://registry.example/",
                fields={
                    "IVOA Identifier": "ivo://example/reg",
                    "RegTAP service endpoint": "https://registry.example/tap",
                },
            )
        ]

    async def _fake_publishers(*_a, **_k):
        return parse_publishers_oai(_MIN_PUBLISHERS)

    monkeypatch.setattr(home, "load_searchables", _fake_load)
    monkeypatch.setattr(home, "load_publishers", _fake_publishers)

    r = await client.get("/")
    assert r.status_code == 200
    assert "Example VO" in r.text
    assert "Example Registry" in r.text
    assert "Full searchable registries" in r.text
    assert "Currently registered publishing registries" in r.text
