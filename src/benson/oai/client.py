"""HTTP client for OAI-PMH registry endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from benson.oai.xmlutil import extract_error_codes
from benson.oai.urls import append_oai_query

if TYPE_CHECKING:
    pass


async def fetch_oai(
    client: httpx.AsyncClient,
    endpoint: str,
    query_fragment: str,
    *,
    timeout: float,
) -> tuple[int, bytes, frozenset[str], str | None]:
    """Return status, raw body, OAI error codes if parsed, XML parse diagnostic."""
    url = append_oai_query(endpoint, query_fragment)
    resp = await client.get(url, follow_redirects=True, timeout=timeout)
    raw = resp.content
    if not raw.strip():
        return resp.status_code, raw, frozenset(), "empty body"

    ctype = resp.headers.get("content-type", "")
    try:
        from lxml import etree

        root = etree.fromstring(raw, etree.XMLParser(no_network=True, resolve_entities=False))
    except Exception as exc:  # noqa: BLE001
        code = raw.decode(errors="replace")[:200] if ctype.startswith("text") else "non-xml"
        return resp.status_code, raw, frozenset(), str(exc) if "xml" in ctype.lower() or raw[:1] == b"<" else code

    return resp.status_code, raw, extract_error_codes(root), None
