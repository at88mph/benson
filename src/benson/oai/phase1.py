"""Phase 1: OAI conformance probes (embedded matrix; optional comply binary)."""

from __future__ import annotations

from pathlib import Path
from subprocess import run
from typing import TYPE_CHECKING

import httpx
from lxml import etree

from benson.config import Settings
from benson.oai.client import fetch_oai
from benson.oai.phase1_tests_data import OAIExplorerCase, OAI_PHASE1_CASES
from benson.xml import results as R

if TYPE_CHECKING:
    pass


def _maybe_comply_xml(endpoint: str, settings: Settings) -> etree._Element | None:
    path = settings.comply_path
    if not path or not Path(path).is_file():
        return None
    try:
        cp = run(
            [path, endpoint],
            capture_output=True,
            text=False,
            timeout=int(settings.harvest_timeout_sec),
            check=False,
        )
    except OSError:
        return None
    if cp.returncode != 0 and not cp.stdout:
        return None
    raw = cp.stdout or b""
    if not raw.strip():
        return None
    try:
        return etree.fromstring(raw, etree.XMLParser(no_network=True, resolve_entities=False))
    except etree.XMLSyntaxError:
        return None


def _error_codes_acceptable(
    codes: frozenset[str],
    expect_codes: frozenset[str] | None,
    ignore_codes: frozenset[str],
    optional_codes: frozenset[str] = frozenset(),
) -> tuple[bool, str, frozenset[str]]:
    ignored = codes & ignore_codes
    if expect_codes is not None:
        if not codes:
            return False, f"Error tag expected but not found : {','.join(sorted(expect_codes))}", frozenset()

        acceptable = expect_codes | ignore_codes
        if not codes <= acceptable:
            bad = sorted(codes - acceptable)
            return False, f"Error code {','.join(bad)} not among expected {{ {','.join(sorted(expect_codes))} }} ", frozenset()

        if codes & expect_codes or codes <= ignore_codes:
            return True, "", ignored

        return False, f"Error tag expected but not found : {','.join(sorted(expect_codes))}", frozenset()

    if optional_codes:
        if not codes:
            return True, "", frozenset()

        acceptable = optional_codes | ignore_codes
        if not codes <= acceptable:
            bad = sorted(codes - acceptable)
            return (
                False,
                f"Error code {','.join(bad)} not among allowed {{ {','.join(sorted(optional_codes))} }} ",
                frozenset(),
            )

        if codes & optional_codes or codes <= ignore_codes:
            return True, "", ignored

        return False, f"Error code not among allowed {{ {','.join(sorted(optional_codes))} }} ", frozenset()

    if codes:
        return False, f"Error tag found but not expected : {','.join(sorted(codes))}", frozenset()
    return True, "", frozenset()


async def build_oai_validation(
    client: httpx.AsyncClient,
    endpoint: str,
    show_status: str,
    *,
    timeout: float,
    settings: Settings,
) -> etree._Element:
    complied = _maybe_comply_xml(endpoint, settings)
    if complied is not None:
        tag = complied.tag
        if tag.startswith("{"):
            tag = tag.split("}", 1)[-1]
        if tag == "OAIValidation":
            return complied

    root = R.oai_validation_root(endpoint.rstrip(), show_status, len(OAI_PHASE1_CASES))

    counted = 0
    for case in OAI_PHASE1_CASES:
        status, _raw, codes, parse_err = await fetch_oai(
            client,
            endpoint,
            case.query_options.lstrip().lstrip("?"),
            timeout=timeout,
        )
        http_ok = 200 <= status < 300

        if not http_ok:
            counted += add_case_fail(root, case, summary_ok=False, msg=f"HTTP {status}")
            continue

        if parse_err:
            counted += add_case_fail(root, case, summary_ok=False, msg=f"invalid XML ({parse_err})")
            continue

        ok, msg, ignored = _error_codes_acceptable(
            codes,
            case.expect_error_one_of,
            case.ignore_errors,
            case.optional_error_one_of,
        )
        if ok:
            counted += probe_pass(root, case, ignored=ignored)
        else:
            counted += probe_fail(root, case, msg)

    root.set("testCount", str(counted))
    return root


def add_case_fail(root: etree._Element, case: OAIExplorerCase, *, summary_ok: bool, msg: str) -> int:
    tq = etree.SubElement(
        root,
        "testQuery",
        name=case.name,
        options=opts_attr(case.query_options),
        role=case.role,
    )
    rows = R.probe_test(False, "http", False, msg)
    rows[0].set("status", "pass" if summary_ok else "fail")
    for r in rows:
        tq.append(r)
    return len(rows)


def probe_pass(root: etree._Element, case: OAIExplorerCase, *, ignored: frozenset[str] = frozenset()) -> int:
    return _probe(root, case, True, "compliant-response", True, "", ignored=ignored)


def probe_fail(root: etree._Element, case: OAIExplorerCase, msg: str) -> int:
    return _probe(root, case, False, "check", False, msg)


def _probe(
    root: etree._Element,
    case: OAIExplorerCase,
    summary_ok: bool,
    item: str,
    ok: bool,
    msg: str,
    *,
    ignored: frozenset[str] = frozenset(),
) -> int:
    tq = etree.SubElement(
        root,
        "testQuery",
        name=case.name,
        options=opts_attr(case.query_options),
        role=case.role,
    )
    if ignored:
        tq.set("ignoredErrors", ",".join(sorted(ignored)))
    text = msg or ("OK" if ok else "failure")
    for r in R.probe_test(summary_ok, item, ok, text):
        tq.append(r)
    return 2


def opts_attr(option_string: str) -> str:
    if option_string.lstrip().startswith("?"):
        return option_string
    q = option_string.lstrip().lstrip("?")
    return "?" + q
