"""Publishing registry JSON store, OAI emit, and registration."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
import httpx
from lxml import etree

_repo = Path(__file__).resolve().parents[1]
os.environ.setdefault("SCHEMA_ROOT", str(_repo / "assets" / "schemas"))
os.environ.setdefault("ASSETS_ROOT", str(_repo / "assets" / "validate"))

from benson.app import create_app, fastapi_app  # noqa: E402
from benson.config import Settings  # noqa: E402
from benson.registry.oai_emit import publishers_to_list_records_xml
from benson.registry.publishers_store import PublisherStore
from benson.registry.registration import eligibility_payload
from benson.registry.registration_policy import eligible_for_registration
from benson.service.rofr_lists import PublisherRegistry, parse_publishers_oai
from benson.session.store import HarvestRun, store
from benson.xml import results as R

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


@pytest_asyncio.fixture
async def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AsyncClient:
    pub = tmp_path / "publishers.json"
    monkeypatch.setenv("PUBLISHERS_REGISTRY_FILE", str(pub))
    settings = Settings.from_env()
    app = create_app()
    core = fastapi_app(app)
    async with httpx.AsyncClient() as hc:
        core.state.settings = settings
        core.state.http_client = hc
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


def test_oai_emit_matches_parse_roundtrip() -> None:
    rows = parse_publishers_oai(_MIN_PUBLISHERS)
    xml = publishers_to_list_records_xml(rows)
    back = parse_publishers_oai(xml)
    assert len(back) == 1
    assert back[0].oai_identifier == "ivo://example/reg"
    assert back[0].harvest_access_url == "https://registry.example/oai"


@pytest.mark.asyncio
async def test_publisher_store_upsert(tmp_path: Path) -> None:
    path = tmp_path / "publishers.json"
    ps = PublisherStore(path)
    await ps.ensure_seed()
    rec = PublisherRegistry(
        oai_identifier="ivo://test/reg",
        title="Test Reg",
        harvest_access_url="https://registry.test/oai",
        registered_at="2026-01-01T00:00:00Z",
        validation_run_id="run1",
    )
    await ps.upsert(rec)
    loaded = await ps.load()
    assert len(loaded) == 1
    assert loaded[0].title == "Test Reg"
    rec.title = "Updated"
    await ps.upsert(rec)
    loaded2 = await ps.load()
    assert len(loaded2) == 1
    assert loaded2[0].title == "Updated"


@pytest.mark.asyncio
async def test_list_publishers_route(client: AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pub = tmp_path / "publishers.json"
    monkeypatch.setenv("PUBLISHERS_REGISTRY_FILE", str(pub))
    ps = PublisherStore(pub)
    await ps.upsert(
        PublisherRegistry(
            oai_identifier="ivo://route/reg",
            title="Route Reg",
            harvest_access_url="https://route.example/oai",
            registered_at="2026-01-01T00:00:00Z",
        )
    )
    r = await client.get("/list-publishers")
    assert r.status_code == 200
    assert "ivo://route/reg" in r.text
    assert "route.example" in r.text


@pytest.mark.asyncio
async def test_publishers_json_api(client: AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pub = tmp_path / "publishers.json"
    monkeypatch.setenv("PUBLISHERS_REGISTRY_FILE", str(pub))
    ps = PublisherStore(pub)
    await ps.upsert(
        PublisherRegistry(
            oai_identifier="ivo://api/reg",
            title="API Reg",
            harvest_access_url="https://api.example/oai",
            registered_at="2026-01-01T00:00:00Z",
        )
    )
    r = await client.get("/api/v1/registry/publishers")
    assert r.status_code == 200
    data = r.json()
    assert data[0]["oai_identifier"] == "ivo://api/reg"


def test_eligible_for_registration_thresholds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REGISTRATION_MAX_FAILURES", "0")
    settings = Settings.from_env()
    root = R.registry_validation_root(status="completed", nfail="0", nwarn="0", nrec="0")
    oai = R.oai_validation_root("https://registry.example/oai", "fail", 1)
    tq = etree.SubElement(oai, "testQuery", name="Identify", options="verb=Identify", role="oai")
    tq.append(R.elt("test", "Not compliant", item="summary", status="fail"))
    root.append(oai)
    run = HarvestRun(
        run_id="x",
        endpoint="https://registry.example/oai",
        builtin_schemas=True,
        cache=False,
        show_status="fail",
        fmt="html",
        error_fmt="html",
        merged_validation=etree.ElementTree(root),
    )
    ok, reason, nf, _nw = eligible_for_registration(run, settings)
    assert not ok
    assert nf == 1
    assert "failure" in reason.lower()


def test_eligibility_payload_report_all_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings.from_env()
    root = R.registry_validation_root(status="completed", nfail="0", nwarn="0", nrec="0")
    harvest = R.harvest_validation_root("https://registry.example/oai", "fail warn rec")
    tq = etree.SubElement(harvest, "testQuery", name="Identify", options="verb=Identify", role="Identify")
    tq.append(R.ri_test(True, "OK"))
    root.append(harvest)
    run = HarvestRun(
        run_id="payload1",
        endpoint="https://registry.example/oai",
        builtin_schemas=False,
        cache=False,
        show_status="fail warn rec",
        fmt="html",
        error_fmt="html",
        merged_validation=etree.ElementTree(root),
    )
    payload = eligibility_payload(run, settings)
    assert payload["report_all_passed"] is True
    assert payload["registration_blocked_by"] == "builtin_schemas"
    assert payload["eligible"] is False


def test_eligibility_payload_all_passed_and_eligible() -> None:
    settings = Settings.from_env()
    root = R.registry_validation_root(status="completed", nfail="0", nwarn="0", nrec="0")
    harvest = R.harvest_validation_root("https://registry.example/oai", "fail warn rec")
    tq = etree.SubElement(harvest, "testQuery", name="Identify", options="verb=Identify", role="Identify")
    tq.append(R.ri_test(True, "OK"))
    root.append(harvest)
    run = HarvestRun(
        run_id="payload2",
        endpoint="https://registry.example/oai",
        builtin_schemas=True,
        cache=False,
        show_status="fail warn rec",
        fmt="html",
        error_fmt="html",
        merged_validation=etree.ElementTree(root),
        identify_oai_identifier="ivo://registry.example/reg",
        identify_title="Example Registry",
    )
    payload = eligibility_payload(run, settings)
    assert payload["report_all_passed"] is True
    assert payload["registration_blocked_by"] is None
    assert payload["eligible"] is True
    assert payload["suggested_oai_identifier"] == "ivo://registry.example/reg"
    assert payload["suggested_title"] == "Example Registry"


@pytest.mark.asyncio
async def test_register_after_validation(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    pub = Path(os.environ["PUBLISHERS_REGISTRY_FILE"])
    ps = PublisherStore(pub)
    await ps.ensure_seed()

    run = HarvestRun(
        run_id="regtest1",
        endpoint="https://newregistry.example/oai",
        builtin_schemas=True,
        cache=True,
        show_status="fail warn rec",
        fmt="html",
        error_fmt="html",
    )
    root = R.registry_validation_root(status="completed", nfail="0", nwarn="0", nrec="0")
    run.merged_validation = etree.ElementTree(root)
    await store.create(run)

    reg = await client.post(
        "/validator/jobs/regtest1/register",
        data={"oai_identifier": "ivo://newregistry/reg", "title": "New Registry"},
    )
    assert reg.status_code == 201
    rows = await ps.load()
    assert any(r.oai_identifier == "ivo://newregistry/reg" for r in rows)
