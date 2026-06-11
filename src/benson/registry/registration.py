"""Register a publishing registry after successful validation."""

from __future__ import annotations

from datetime import UTC, datetime

from benson.config import Settings
from benson.registry.publishers_store import PublisherStore, normalize_endpoint
from benson.registry.registration_policy import eligible_for_registration, registration_blocked_by
from benson.service.rofr_lists import PublisherRegistry
from benson.session.store import HarvestRun, store


class RegistrationError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


async def register_publisher(
    run_id: str,
    *,
    oai_identifier: str,
    title: str,
    settings: Settings,
) -> PublisherRegistry:
    run = await store.get(run_id)
    if run is None:
        raise RegistrationError("Validation session not found or expired.", status_code=404)

    ok, reason, _nf, _nw = eligible_for_registration(run, settings)
    if not ok:
        raise RegistrationError(reason, status_code=409)

    oid = oai_identifier.strip()
    t = title.strip()
    if not oid:
        raise RegistrationError("IVOA identifier is required.")
    if not t:
        raise RegistrationError("Title is required.")

    endpoint = normalize_endpoint(run.endpoint)
    pub_store = PublisherStore.from_settings(settings)
    await pub_store.ensure_seed()

    if await pub_store.find_by_identifier(oid):
        raise RegistrationError(f"Identifier already registered: {oid}", status_code=409)
    existing = await pub_store.find_by_endpoint(run.endpoint)
    if existing is not None:
        raise RegistrationError(
            f"OAI endpoint already registered as {existing.oai_identifier}.",
            status_code=409,
        )

    registered_at = datetime.now(UTC).isoformat()
    live_oai_identifier = (run.identify_oai_identifier or "").strip() or oid
    live_title = (run.identify_title or "").strip() or t
    check_status = "ok"
    check_detail = None
    if live_oai_identifier != oid:
        check_status = "identifier_mismatch"
        check_detail = f"live identifier is {live_oai_identifier}"

    record = PublisherRegistry(
        oai_identifier=oid,
        title=t,
        harvest_access_url=run.endpoint.strip().rstrip("/") or run.endpoint.strip(),
        registered_at=registered_at,
        validation_run_id=run.run_id,
        last_checked_at=registered_at,
        check_status=check_status,
        live_oai_identifier=live_oai_identifier,
        live_title=live_title,
        check_detail=check_detail,
    )
    return await pub_store.upsert(record)


def eligibility_payload(run: HarvestRun, settings: Settings) -> dict[str, object]:
    ok, reason, nfail, nwarn = eligible_for_registration(run, settings)
    blocked_by = registration_blocked_by(run, settings)
    return {
        "eligible": ok,
        "reason": reason,
        "nfail": nfail,
        "nwarn": nwarn,
        "report_all_passed": nfail == 0 and nwarn == 0,
        "registration_blocked_by": blocked_by,
        "endpoint": run.endpoint,
        "builtin_schemas": run.builtin_schemas,
        "suggested_oai_identifier": run.identify_oai_identifier,
        "suggested_title": run.identify_title,
    }
