"""Async validator job API tests."""

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
from benson.session.store import store  # noqa: E402


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
async def test_create_job_returns_immediately(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _noop(*_a, **_k):
        return None

    monkeypatch.setattr("benson.http.validator.spawn_harvest_validation", _noop)

    resp = await client.post(
        "/validator/jobs",
        data={"endpoint": "https://registry.example/oai", "builtin_schemas": "true"},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["state"] == "pending"
    assert body["run_id"]
    assert body["status_url"].startswith("/validator/jobs/")


@pytest.mark.asyncio
async def test_job_status_and_result_not_ready(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("benson.http.validator.spawn_harvest_validation", lambda *a, **k: None)

    created = await client.post(
        "/validator/jobs",
        data={"endpoint": "https://registry.example/oai"},
    )
    run_id = created.json()["run_id"]

    status = await client.get(f"/validator/jobs/{run_id}")
    assert status.status_code == 200
    assert status.json()["state"] in ("pending", "running")

    result = await client.get(f"/validator/jobs/{run_id}/result")
    assert result.status_code == 409


@pytest.mark.asyncio
async def test_validator_page_includes_progress_script(client: AsyncClient) -> None:
    resp = await client.get("/validator")
    assert resp.status_code == 200
    assert "val-progress" in resp.text
    assert "validator-watch.js" in resp.text


@pytest.mark.asyncio
async def test_regvalidate_alias(client: AsyncClient) -> None:
    resp = await client.get("/regvalidate")
    assert resp.status_code == 200
    assert "Registry validator" in resp.text
    assert 'href="/"' in resp.text


@pytest.mark.asyncio
async def test_job_result_when_complete(client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from lxml import etree

    from benson.http.harvest import new_run_from_query
    from benson.xml import results as R

    monkeypatch.setattr("benson.http.validator.spawn_harvest_validation", lambda *a, **k: None)

    created = await client.post("/validator/jobs", data={"endpoint": "https://registry.example/oai"})
    run_id = created.json()["run_id"]
    run = await store.get(run_id)
    assert run is not None
    root = R.registry_validation_root(status="completed", nfail="0", nwarn="0", nrec="0")
    harvest = R.harvest_validation_root("https://registry.example/oai", "fail warn rec")
    root.append(harvest)
    run.merged_validation = etree.ElementTree(root)

    result = await client.get(f"/validator/jobs/{run_id}/result")
    assert result.status_code == 200
    assert "IVOA harvest profile" in result.text
