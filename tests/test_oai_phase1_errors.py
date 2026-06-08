"""Tests for OAI phase-1 error-code matching."""

from __future__ import annotations

from lxml import etree

from benson.oai.phase1 import _error_codes_acceptable
from benson.oai.xmlutil import extract_error_code, extract_error_codes

OAI = "http://www.openarchives.org/OAI/2.0/"


def _error_xml(*codes: str) -> etree._Element:
    root = etree.Element(f"{{{OAI}}}OAI-PMH")
    for code in codes:
        etree.SubElement(root, f"{{{OAI}}}error", code=code)
    return root


def test_extract_error_codes_collects_all_errors() -> None:
    root = _error_xml("badResumptionToken", "badArgument")
    assert extract_error_codes(root) == frozenset({"badResumptionToken", "badArgument"})
    assert extract_error_code(root) in {"badResumptionToken", "badArgument"}


def test_expected_code_passes() -> None:
    ok, msg, ignored = _error_codes_acceptable(
        frozenset({"badResumptionToken"}),
        frozenset({"badResumptionToken"}),
        frozenset({"badArgument"}),
    )
    assert ok
    assert msg == ""
    assert ignored == frozenset()


def test_ignored_code_alone_passes() -> None:
    ok, msg, ignored = _error_codes_acceptable(
        frozenset({"badArgument"}),
        frozenset({"badResumptionToken"}),
        frozenset({"badArgument"}),
    )
    assert ok
    assert msg == ""
    assert ignored == frozenset({"badArgument"})


def test_ignored_code_alongside_expected() -> None:
    ok, msg, ignored = _error_codes_acceptable(
        frozenset({"badResumptionToken", "badArgument"}),
        frozenset({"badResumptionToken"}),
        frozenset({"badArgument"}),
    )
    assert ok
    assert ignored == frozenset({"badArgument"})


def test_unexpected_code_fails() -> None:
    ok, msg, ignored = _error_codes_acceptable(
        frozenset({"badVerb"}),
        frozenset({"badResumptionToken"}),
        frozenset({"badArgument"}),
    )
    assert not ok
    assert "badVerb" in msg
    assert ignored == frozenset()


def test_no_error_expected_rejects_any_code() -> None:
    ok, msg, ignored = _error_codes_acceptable(frozenset({"badArgument"}), None, frozenset())
    assert not ok
    assert "badArgument" in msg
    assert ignored == frozenset()


def test_optional_error_absent_passes() -> None:
    ok, msg, ignored = _error_codes_acceptable(
        frozenset(),
        None,
        frozenset(),
        frozenset({"noRecordsMatch", "badArgument"}),
    )
    assert ok
    assert msg == ""
    assert ignored == frozenset()


def test_optional_error_matching_code_passes() -> None:
    ok, msg, ignored = _error_codes_acceptable(
        frozenset({"noRecordsMatch"}),
        None,
        frozenset(),
        frozenset({"noRecordsMatch", "badArgument"}),
    )
    assert ok
    assert msg == ""
    assert ignored == frozenset()


def test_optional_error_wrong_code_fails() -> None:
    ok, msg, ignored = _error_codes_acceptable(
        frozenset({"badVerb"}),
        None,
        frozenset(),
        frozenset({"noRecordsMatch", "badArgument"}),
    )
    assert not ok
    assert "badVerb" in msg
    assert ignored == frozenset()


def test_optional_error_ignored_code_alone_passes() -> None:
    ok, msg, ignored = _error_codes_acceptable(
        frozenset({"badArgument"}),
        None,
        frozenset({"badArgument"}),
        frozenset({"noRecordsMatch"}),
    )
    assert ok
    assert msg == ""
    assert ignored == frozenset({"badArgument"})
