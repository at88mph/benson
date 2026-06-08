"""Phase 3 ListRecords harvest behavior."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from lxml import etree

from benson.config import Settings
from benson.http.validation_report import render_validation_report, validation_result_counts
from benson.oai.phase3 import (
    OAI_NS,
    _is_deleted_record,
    append_harvest_failures,
    harvest_voresource_documents,
)
from benson.xml import results as R

_VOR_INNER = b'<Resource xmlns="http://www.ivoa.net/xml/VOResource/v1.0"/>'

_LIST_PAGE = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <ListRecords>
    <record>
      <header status="deleted">
        <identifier>ivo://example/deleted</identifier>
      </header>
    </record>
    <record>
      <header>
        <identifier>ivo://example/active-1</identifier>
      </header>
      <metadata>
        {_VOR_INNER.decode()}
      </metadata>
    </record>
    <record>
      <header>
        <identifier>ivo://example/empty-md</identifier>
      </header>
      <metadata/>
    </record>
    <record>
      <header>
        <identifier>ivo://example/active-2</identifier>
      </header>
      <metadata>
        {_VOR_INNER.decode()}
      </metadata>
    </record>
  </ListRecords>
</OAI-PMH>
""".encode()


def _record_xml(header_status: str | None, *, ident: str, with_metadata: bool) -> str:
    status_attr = f' status="{header_status}"' if header_status else ""
    md = f"<metadata>{_VOR_INNER.decode()}</metadata>" if with_metadata else ""
    return (
        f"<record><header{status_attr}>"
        f"<identifier>{ident}</identifier></header>{md}</record>"
    )


def test_is_deleted_record() -> None:
    deleted = etree.fromstring(
        f'<record xmlns="{OAI_NS}"><header status="deleted">'
        f"<identifier>ivo://x/y</identifier></header></record>"
    )
    active = etree.fromstring(
        f'<record xmlns="{OAI_NS}"><header>'
        f"<identifier>ivo://x/y</identifier></header></record>"
    )
    assert _is_deleted_record(deleted)
    assert not _is_deleted_record(active)


@pytest.mark.asyncio
async def test_harvest_skips_deleted_records() -> None:
    settings = Settings.from_env()

    async def fake_fetch(_client, _endpoint, _query, *, timeout):
        return 200, _LIST_PAGE, frozenset(), None

    async with httpx.AsyncClient() as client:
        with patch("benson.oai.phase3.fetch_oai", side_effect=fake_fetch):
            collected, stats = await harvest_voresource_documents(
                client,
                "https://registry.example/oai",
                max_records=2,
                timeout=30.0,
                builtin_schemas=False,
                settings=settings,
            )

    assert stats.nfail == 1
    assert len(stats.failures) == 1
    assert stats.failures[0] == ("ivo://example/empty-md", "ListRecords record has no metadata")
    assert set(collected) == {"ivo://example/active-1", "ivo://example/active-2"}
    assert "ivo://example/deleted" not in collected
    assert "ivo://example/empty-md" not in collected


@pytest.mark.asyncio
async def test_harvest_deleted_without_metadata_is_not_failure() -> None:
    settings = Settings.from_env()
    page = f"""<?xml version="1.0" encoding="UTF-8"?>
<OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
  <ListRecords>
    {_record_xml("deleted", ident="ivo://example/tombstone", with_metadata=False)}
    {_record_xml(None, ident="ivo://example/ok", with_metadata=True)}
  </ListRecords>
</OAI-PMH>
""".encode()

    fetch = AsyncMock(return_value=(200, page, frozenset(), None))
    async with httpx.AsyncClient() as client:
        with patch("benson.oai.phase3.fetch_oai", fetch):
            collected, stats = await harvest_voresource_documents(
                client,
                "https://registry.example/oai",
                max_records=1,
                timeout=30.0,
                builtin_schemas=False,
                settings=settings,
            )

    assert stats.nfail == 0
    assert stats.failures == []
    assert list(collected) == ["ivo://example/ok"]


def test_harvest_failures_visible_in_report() -> None:
    vor_root = R.vor_validation_root("fail warn rec")
    append_harvest_failures(
        vor_root,
        [("ivo://example/empty-md", "ListRecords record has no metadata")],
    )
    merged = R.registry_validation_root(status="completed", nfail="0", nwarn="0", nrec="0")
    merged.append(vor_root)
    nfail, nwarn, npass = validation_result_counts(merged)
    assert nfail == 1
    assert nwarn == 0
    assert npass == 0
    html = render_validation_report(etree.ElementTree(merged))
    assert "ListRecords record has no metadata" in html
    assert "val-summary--fail" in html
