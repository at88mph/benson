"""Tests for publisher liveness checks via OAI Identify."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from benson.registry.publishers_check import PublisherCheckResult, check_publishers
from benson.registry.publishers_store import PublisherStore
from benson.service.rofr_lists import (
    PublisherRegistry,
    format_utc_display,
    render_publishers_section,
)

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
_CADC_IDENTIFY = (_FIXTURES / "cadc_identify.xml").read_bytes()
_CADC_ENDPOINT = "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/oai"
_CADC_ID = "ivo://cadc.nrc.ca/registry"

_IDENTIFY_NO_REGISTRY = b"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>2026-01-01T00:00:00Z</responseDate>
  <request verb="Identify">https://registry.example/oai</request>
  <Identify>
    <repositoryName>Example</repositoryName>
    <baseURL>https://registry.example/oai</baseURL>
    <protocolVersion>2.0</protocolVersion>
    <adminEmail>admin@example.org</adminEmail>
  </Identify>
</OAI-PMH>
"""

_OAI_ERROR = b"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <responseDate>2026-01-01T00:00:00Z</responseDate>
  <request verb="Identify">https://registry.example/oai</request>
  <error code="badVerb">Illegal OAI verb</error>
</OAI-PMH>
"""


def _publisher(
    *,
    oai_identifier: str = _CADC_ID,
    harvest_access_url: str = _CADC_ENDPOINT,
) -> PublisherRegistry:
    return PublisherRegistry(
        oai_identifier=oai_identifier,
        title="CADC Registry",
        harvest_access_url=harvest_access_url,
        registered_at="2026-01-01T00:00:00Z",
    )


async def _run_check(
    tmp_path: Path,
    publisher: PublisherRegistry,
    fetch_side_effect,
) -> tuple[list[PublisherCheckResult], PublisherStore]:
    pub_file = tmp_path / "publishers.json"
    store = PublisherStore(pub_file)
    await store.upsert(publisher)
    client = AsyncMock(spec=httpx.AsyncClient)
    with patch(
        "benson.registry.publishers_check.fetch_oai",
        new=AsyncMock(side_effect=fetch_side_effect),
    ):
        results = await check_publishers(client, store, timeout=30.0, concurrency=1)
    return results, store


@pytest.mark.asyncio
async def test_check_publisher_ok(tmp_path: Path) -> None:
    async def fetch_ok(*_args, **_kwargs):
        return 200, _CADC_IDENTIFY, frozenset(), None

    results, _store = await _run_check(tmp_path, _publisher(), fetch_ok)
    assert len(results) == 1
    assert results[0].status == "ok"
    assert results[0].live_oai_identifier == _CADC_ID
    assert results[0].live_title == "CADC Registry"


@pytest.mark.asyncio
async def test_check_publisher_unreachable(tmp_path: Path) -> None:
    async def fetch_fail(*_args, **_kwargs):
        return 503, b"", frozenset(), "empty body"

    results, _store = await _run_check(tmp_path, _publisher(), fetch_fail)
    assert results[0].status == "unreachable"
    assert "HTTP 503" in (results[0].detail or "")


@pytest.mark.asyncio
async def test_check_publisher_network_error(tmp_path: Path) -> None:
    async def fetch_error(*_args, **_kwargs):
        raise httpx.ConnectError("connection refused")

    results, _store = await _run_check(tmp_path, _publisher(), fetch_error)
    assert results[0].status == "unreachable"
    assert "connection refused" in (results[0].detail or "")


@pytest.mark.asyncio
async def test_check_publisher_oai_error(tmp_path: Path) -> None:
    async def fetch_oai_error(*_args, **_kwargs):
        return 200, _OAI_ERROR, frozenset({"badVerb"}), None

    results, _store = await _run_check(tmp_path, _publisher(), fetch_oai_error)
    assert results[0].status == "invalid_response"
    assert "badVerb" in (results[0].detail or "")


@pytest.mark.asyncio
async def test_check_publisher_no_registry(tmp_path: Path) -> None:
    async def fetch_no_reg(*_args, **_kwargs):
        return 200, _IDENTIFY_NO_REGISTRY, frozenset(), None

    results, _store = await _run_check(tmp_path, _publisher(), fetch_no_reg)
    assert results[0].status == "no_registry"


@pytest.mark.asyncio
async def test_check_publisher_identifier_mismatch(tmp_path: Path) -> None:
    async def fetch_ok(*_args, **_kwargs):
        return 200, _CADC_IDENTIFY, frozenset(), None

    pub = _publisher(oai_identifier="ivo://other/registry")
    results, _store = await _run_check(tmp_path, pub, fetch_ok)
    assert results[0].status == "identifier_mismatch"
    assert results[0].live_oai_identifier == _CADC_ID


@pytest.mark.asyncio
async def test_check_publisher_no_endpoint(tmp_path: Path) -> None:
    pub_file = tmp_path / "publishers.json"
    pub_file.write_text(
        json.dumps(
            {
                "version": 1,
                "publishers": [
                    {
                        "oai_identifier": "ivo://no-endpoint/reg",
                        "title": "No Endpoint",
                        "registered_at": "2026-01-01T00:00:00Z",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    store = PublisherStore(pub_file)
    client = AsyncMock(spec=httpx.AsyncClient)
    with patch(
        "benson.registry.publishers_check.fetch_oai",
        new=AsyncMock(),
    ) as mock_fetch:
        results = await check_publishers(client, store, timeout=30.0, concurrency=1)
    mock_fetch.assert_not_called()
    assert results[0].status == "no_endpoint"


@pytest.mark.asyncio
async def test_annotate_checks_persists(tmp_path: Path) -> None:
    pub_file = tmp_path / "publishers.json"
    store = PublisherStore(pub_file)
    await store.upsert(_publisher())
    result = PublisherCheckResult(
        oai_identifier=_CADC_ID,
        harvest_access_url=_CADC_ENDPOINT,
        status="ok",
        live_oai_identifier=_CADC_ID,
        live_title="CADC Registry",
        detail=None,
        checked_at="2026-06-11T06:00:00+00:00",
    )
    await store.annotate_checks([result])
    loaded = await store.load()
    assert loaded[0].check_status == "ok"
    assert loaded[0].last_checked_at == "2026-06-11T06:00:00+00:00"
    assert loaded[0].live_oai_identifier == _CADC_ID

    raw = json.loads(pub_file.read_text(encoding="utf-8"))
    assert raw["publishers"][0]["last_checked_at"] == "2026-06-11T06:00:00+00:00"
    assert " UTC" not in raw["publishers"][0]["last_checked_at"]


@pytest.mark.asyncio
async def test_upsert_preserves_check_fields(tmp_path: Path) -> None:
    store = PublisherStore(tmp_path / "publishers.json")
    rec = _publisher()
    await store.upsert(rec)
    await store.annotate_checks(
        [
            PublisherCheckResult(
                oai_identifier=_CADC_ID,
                harvest_access_url=_CADC_ENDPOINT,
                status="ok",
                live_oai_identifier=_CADC_ID,
                live_title="CADC Registry",
                detail=None,
                checked_at="2026-06-11T06:00:00Z",
            )
        ]
    )
    rec.title = "Renamed"
    await store.upsert(rec)
    loaded = await store.load()
    assert loaded[0].title == "Renamed"
    assert loaded[0].check_status == "ok"
    assert loaded[0].last_checked_at == "2026-06-11T06:00:00Z"


def test_format_utc_display() -> None:
    assert format_utc_display("2026-06-11T06:00:00Z") == "2026-06-11T06:00:00Z UTC"
    assert format_utc_display("2026-06-11T06:00:00+00:00") == "2026-06-11T06:00:00Z UTC"


def test_render_publishers_section_utc_suffix() -> None:
    html = render_publishers_section(
        [
            PublisherRegistry(
                oai_identifier=_CADC_ID,
                title="CADC Registry",
                harvest_access_url=_CADC_ENDPOINT,
                last_checked_at="2026-06-11T06:00:00Z",
                check_status="ok",
            )
        ]
    )
    assert "2026-06-11T06:00:00Z UTC" in html
    assert "Last check" in html
    assert html.count(" UTC") == 1


def test_render_publishers_section_omits_unchecked() -> None:
    html = render_publishers_section([_publisher()])
    assert "Last check" not in html
    assert " UTC" not in html
