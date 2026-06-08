"""Start and inspect background harvest validation jobs."""

from __future__ import annotations

import asyncio
import logging

import httpx

from benson.config import Settings
from benson.service import harvest_runner
from benson.session.store import HarvestRun

logger = logging.getLogger("benson.service.validation_job")

PHASE_LABELS: dict[str, str] = {
    "start": "Starting",
    "oai": "OAI-PMH conformance",
    "ivoa": "IVOA harvest profile",
    "vor": "VOResource records",
    "done": "Finished",
}

PHASE_ORDER: tuple[str, ...] = ("oai", "ivoa", "vor")
PHASE_STEP_LABELS: dict[str, str] = {
    "oai": "OAI-PMH",
    "ivoa": "IVOA harvest",
    "vor": "VOResource",
}


def job_state(run: HarvestRun) -> str:
    if run.canceled:
        return "canceled"
    if run.validation_error:
        return "error"
    if run.merged_validation is not None:
        return "complete"
    if run.background_task is not None and not run.background_task.done():
        return "running"
    if run.background_task is not None and run.background_task.done() and run.merged_validation is None:
        return "error" if run.validation_error else "complete"
    return "pending"


def latest_message(run: HarvestRun) -> str:
    if run.validation_error:
        return run.validation_error
    if run.status_rows:
        return run.status_rows[-1].get("message", "")
    return "Waiting to start…"


def latest_phase(run: HarvestRun) -> str:
    for row in reversed(run.status_rows):
        phase = row.get("phase")
        if phase:
            return phase
    return ""


def phase_step_states(run: HarvestRun) -> list[dict[str, str]]:
    state = job_state(run)
    completed = {phase: False for phase in PHASE_ORDER}
    active = ""
    for row in run.status_rows:
        phase = row.get("phase")
        if phase not in completed:
            continue
        if row.get("status") == "completed":
            completed[phase] = True
        elif row.get("status") == "running":
            active = phase

    if state == "complete":
        completed = dict.fromkeys(PHASE_ORDER, True)
        active = ""

    error_at = ""
    if state == "error":
        error_at = active or latest_phase(run)
        if error_at not in PHASE_ORDER:
            error_at = PHASE_ORDER[0]

    steps: list[dict[str, str]] = []
    for phase in PHASE_ORDER:
        if state == "complete" or completed[phase]:
            step_status = "complete"
        elif state == "error" and phase == error_at:
            step_status = "error"
        elif active == phase or (
            not active
            and state in ("pending", "running")
            and phase == PHASE_ORDER[0]
            and not any(completed.values())
        ):
            step_status = "active"
        else:
            step_status = "pending"
        steps.append({"id": phase, "label": PHASE_STEP_LABELS[phase], "status": step_status})
    return steps


def progress_percent(run: HarvestRun) -> int:
    state = job_state(run)
    steps = phase_step_states(run)
    if state == "complete":
        return 100
    total = len(steps)
    done = sum(1 for step in steps if step["status"] == "complete")
    active = any(step["status"] == "active" for step in steps)
    pct = (done / total) * 100
    if active:
        pct += (0.45 / total) * 100
    return min(99, max(5, int(pct)))


def spawn_harvest_validation(
    run: HarvestRun,
    *,
    settings: Settings,
    client: httpx.AsyncClient,
    max_records: int = 5,
) -> None:
    if run.background_task is not None and not run.background_task.done():
        return

    async def worker() -> None:
        try:
            run.add_status_row(
                message="Validation started",
                done="false",
                ok="true",
                status="running",
                phase="start",
            )
            await harvest_runner.execute_harvest_validation(
                run,
                settings=settings,
                client=client,
                max_records=max_records,
            )
            run.add_status_row(
                message="Validation complete",
                done="true",
                ok="true",
                status="completed",
                phase="done",
            )
        except asyncio.CancelledError:
            run.add_status_row(
                message="Validation canceled",
                done="true",
                ok="false",
                status="canceled",
                phase="done",
            )
            raise
        except Exception as exc:
            logger.exception("Validation job failed run_id=%s", run.run_id)
            run.validation_error = str(exc)
            run.add_status_row(
                message=str(exc),
                done="true",
                ok="false",
                status="error",
                phase="done",
            )

    run.background_task = asyncio.create_task(worker())


def status_payload(run: HarvestRun) -> dict[str, object]:
    phase = latest_phase(run)
    return {
        "run_id": run.run_id,
        "endpoint": run.endpoint,
        "state": job_state(run),
        "phase": phase,
        "phase_label": PHASE_LABELS.get(phase, phase or "Working"),
        "message": latest_message(run),
        "progress_percent": progress_percent(run),
        "phases": phase_step_states(run),
        "done": job_state(run) in ("complete", "error", "canceled"),
        "steps": list(run.status_rows),
        "error": run.validation_error,
        "result_url": f"/validator/jobs/{run.run_id}/result",
    }
