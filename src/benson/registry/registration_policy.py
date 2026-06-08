"""Rules for whether a completed validation run may be registered."""

from __future__ import annotations

from benson.config import Settings
from benson.http.validation_report import validation_result_counts
from benson.session.store import HarvestRun


def _validation_counts(run: HarvestRun) -> tuple[int, int]:
    if run.merged_validation is None:
        return 0, 0
    nfail, nwarn, _npass = validation_result_counts(run.merged_validation.getroot())
    return nfail, nwarn


def registration_blocked_by(run: HarvestRun, settings: Settings) -> str | None:
    if run.merged_validation is None:
        return "incomplete"
    if run.validation_error:
        return "incomplete"
    if settings.registration_require_builtin_schemas and not run.builtin_schemas:
        return "builtin_schemas"
    nfail, nwarn = _validation_counts(run)
    if nfail > settings.registration_max_failures:
        return "failures"
    if nwarn > settings.registration_max_warnings:
        return "warnings"
    return None


def eligible_for_registration(run: HarvestRun, settings: Settings) -> tuple[bool, str, int, int]:
    """Return (eligible, reason, nfail, nwarn)."""
    if run.merged_validation is None:
        return False, "Validation is not complete.", 0, 0
    if run.validation_error:
        return False, run.validation_error, 0, 0
    if settings.registration_require_builtin_schemas and not run.builtin_schemas:
        return False, "Built-in XSD schemas are required for registration.", 0, 0

    nfail, nwarn = _validation_counts(run)
    if nfail > settings.registration_max_failures:
        return (
            False,
            f"Validation has {nfail} failure(s); at most {settings.registration_max_failures} allowed.",
            nfail,
            nwarn,
        )
    if nwarn > settings.registration_max_warnings:
        return (
            False,
            f"Validation has {nwarn} warning(s); at most {settings.registration_max_warnings} allowed.",
            nfail,
            nwarn,
        )
    return True, "Eligible for registration.", nfail, nwarn
