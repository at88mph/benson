"""Standalone VOResource multipart validation."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, Response
from lxml import etree

from benson.config import Settings
from benson.service import harvest_runner

router = APIRouter(prefix="/registry-validate", tags=["registry-validate"])

MAX_FILES = 10


def format_output(root: etree._Element, fmt: str) -> tuple[bytes, str]:  # noqa: SLF001
    tree = etree.ElementTree(root)
    data = etree.tostring(tree.getroot(), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    if fmt == "xml":
        return data, "application/xml"
    if fmt == "text":
        return data, "text/plain; charset=utf-8"
    escaped = data.decode(errors="replace").replace("&", "&amp;").replace("<", "&lt;")
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'/>"
        "<title>VOResource</title></head><body><pre>"
        + escaped
        + "</pre></body></html>"
    )
    return html.encode(), "text/html"


@router.post("/voresource")
async def voresource_validater(
    request: Request,
    record: list[UploadFile] | None = File(None),
    recordURL: str | None = Form(None),
    format: str | None = Form("html"),  # noqa: A002
    show: str | None = Form(None),
) -> Response:
    settings: Settings = request.app.state.settings
    client: httpx.AsyncClient = request.app.state.http_client
    fmt = (format or "html").lower()
    show_s = show or "fail warn rec"

    records: dict[str, bytes] = {}
    dup = 0
    if record:
        for uf in record[:MAX_FILES]:
            raw = await uf.read()
            nm = uf.filename or "anonymous.xml"
            key = nm
            while key in records:
                dup += 1
                key = f"{nm}:{dup}"
            records[key] = raw
    if recordURL:
        for url in recordURL.split():
            u = url.strip()
            parsed = urlparse(u)
            if parsed.scheme == "file":
                raise HTTPException(status_code=400, detail="file: URLs not allowed")
            if parsed.scheme not in ("http", "https"):
                continue
            resp = await client.get(u, timeout=60.0)
            if resp.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"fetch HTTP {resp.status_code}")
            key = u
            while key in records:
                dup += 1
                key = f"{u}:{dup}"
            records[key] = resp.content

    if not records:
        raise HTTPException(status_code=400, detail="record or recordURL required")

    root_el, _stats = harvest_runner.phase3_validate_only(records, show_s, True, settings)
    body, ctype = format_output(root_el, fmt)
    return Response(content=body, media_type=ctype)
