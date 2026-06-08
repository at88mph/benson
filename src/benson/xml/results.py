"""Compose OAIValidation / HarvestValidation / RegistryValidation / VOResourceValidation fragments."""

from __future__ import annotations

from lxml import etree

_NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"


def elt(tag: str, text: str | None = None, **attrib: str) -> etree._Element:
    e = etree.Element(tag, attrib)
    if text is not None:
        e.text = text
    return e


def oai_validation_root(base_url: str, show_status: str, test_count: int) -> etree._Element:
    return elt(
        "OAIValidation",
        baseURL=base_url,
        showStatus=show_status,
        testCount=str(test_count),
    )


def harvest_validation_root(base_url: str, show_status: str) -> etree._Element:
    return elt(
        "HarvestValidation",
        baseURL=base_url,
        showStatus=show_status,
    )


def registry_validation_root(*, status: str, nfail: str, nwarn: str, nrec: str) -> etree._Element:
    return elt(
        "RegistryValidation",
        status=status,
        nfail=nfail,
        nwarn=nwarn,
        nrec=nrec,
    )


def vor_validation_root(show_status: str) -> etree._Element:
    return elt("VOResourceValidation", showStatus=show_status)


def probe_test(summary_ok: bool, detail_item: str, detail_ok: bool, detail_msg: str) -> list[etree._Element]:
    return [
        elt(
            "test",
            "Operation must be compliant with OAI-PMH standard",
            item="summary",
            status="pass" if summary_ok else "fail",
        ),
        elt("test", detail_msg, item=detail_item, status="pass" if detail_ok else "fail"),
    ]


def ri_test(ok: bool, message: str) -> etree._Element:
    t = etree.Element(
        "test",
        nsmap={"xsi": _NS_XSI},
        item="RI3.1.1",
        status="pass" if ok else "fail",
    )
    t.text = message
    return t
