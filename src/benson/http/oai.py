"""OAI-PMH endpoint for the IVOA standards catalog."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from benson.oai.server import dispatch_oai_verb, parse_query_params
from benson.registry.standards_store import StandardsStore

router = APIRouter(tags=["oai"])


@router.get("/oai", name="oai")
async def oai_endpoint(request: Request) -> Response:
    settings = request.app.state.settings
    store = StandardsStore.from_settings(settings)
    base_url = str(request.url_for("oai"))
    raw = parse_query_params(request.query_params)
    body = dispatch_oai_verb(settings, store, base_url, raw)
    return Response(content=body, media_type="application/xml; charset=utf-8")
