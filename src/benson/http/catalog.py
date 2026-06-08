"""Public catalog endpoints for RofR lists."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from benson.registry.oai_emit import publishers_to_list_records_xml
from benson.registry.publishers_store import PublisherStore

router = APIRouter(tags=["catalog"])


@router.get("/list-publishers")
async def list_publishers(request: Request) -> Response:
    settings = request.app.state.settings
    store = PublisherStore.from_settings(settings)
    await store.ensure_seed()
    records = await store.load()
    body = publishers_to_list_records_xml(records)
    return Response(content=body, media_type="application/xml; charset=utf-8")


@router.get("/list-searchables", response_class=HTMLResponse, include_in_schema=False)
async def list_searchables_stub() -> HTMLResponse:
    """Reserved; searchables are loaded on the home page from RegTAP/cache today."""
    return HTMLResponse(
        "<p>Searchables catalog is not exposed here yet. Use the home page or RegTAP sync.</p>",
        status_code=501,
    )
