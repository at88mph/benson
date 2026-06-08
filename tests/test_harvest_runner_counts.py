"""Merged validation root counts align with HTML report logic."""

from __future__ import annotations

from copy import deepcopy

from benson.http.validation_report import validation_result_counts
from benson.oai import phase3
from benson.xml import results as R


def test_merged_root_nfail_matches_report_counts() -> None:
    oai = R.oai_validation_root("https://registry.example/oai", "fail warn rec", 1)
    ivoa = R.harvest_validation_root("https://registry.example/oai", "fail warn rec")
    vor = R.vor_validation_root("fail warn rec")
    phase3.append_harvest_failures(
        vor,
        [("ivo://example/empty-md", "ListRecords record has no metadata")],
    )

    rr = R.registry_validation_root(status="completed", nfail="0", nwarn="0", nrec="0")
    rr.append(deepcopy(oai))
    rr.append(deepcopy(ivoa))
    rr.append(deepcopy(vor))

    nfail, nwarn, _npass = validation_result_counts(rr)
    rr.set("nfail", str(nfail))
    rr.set("nwarn", str(nwarn))

    assert nfail == 1
    assert int(rr.get("nfail", "0")) == nfail
    assert int(rr.get("nwarn", "0")) == nwarn
