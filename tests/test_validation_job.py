"""Validation job progress helpers."""

from __future__ import annotations

from benson.http.harvest import new_run_from_query
from benson.service.validation_job import job_state, phase_step_states, progress_percent, status_payload
from benson.session.store import HarvestRun


def _run_with_steps(rows: list[dict[str, str]]) -> HarvestRun:
    run = new_run_from_query({"cache": "true"}, "https://registry.example/oai")
    for row in rows:
        run.add_status_row(**row)
    return run


def test_progress_percent_complete() -> None:
    run = _run_with_steps([
        {"message": "done", "status": "completed", "phase": "done", "done": "true", "ok": "true"},
    ])
    run.merged_validation = object()  # type: ignore[assignment]
    assert progress_percent(run) == 100
    assert job_state(run) == "complete"


def test_phase_step_states_active_oai() -> None:
    run = _run_with_steps([
        {"message": "OAI started", "status": "running", "phase": "oai", "done": "false", "ok": "true"},
    ])
    steps = phase_step_states(run)
    assert steps[0]["status"] == "active"
    assert steps[1]["status"] == "pending"
    assert progress_percent(run) > 5


def test_status_payload_includes_progress_fields() -> None:
    run = _run_with_steps([
        {"message": "IVOA started", "status": "running", "phase": "ivoa", "done": "false", "ok": "true"},
    ])
    payload = status_payload(run)
    assert "progress_percent" in payload
    assert "phases" in payload
    assert len(payload["phases"]) == 3  # type: ignore[arg-type]
