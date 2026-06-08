"""Minimal OAI-PMH response parsing."""

from __future__ import annotations

from lxml import etree

OAI_NS = "http://www.openarchives.org/OAI/2.0/"


def _error_elements(root: etree._Element) -> list[etree._Element]:  # noqa: SLF001
    found: list[etree._Element] = []
    seen: set[int] = set()
    for el in root.iter():
        tag = el.tag
        if isinstance(tag, bytes):
            tag = tag.decode("utf-8", errors="replace")
        elif not isinstance(tag, str):
            continue
        base = tag.rsplit("}", 1)[-1] if tag.startswith("{") else tag
        if base == "error" and id(el) not in seen:
            seen.add(id(el))
            found.append(el)
    return found


def extract_error_codes(root: etree._Element | None) -> frozenset[str]:  # noqa: SLF001
    """Return all OAI error @code values found in the response."""
    if root is None:
        return frozenset()
    return frozenset(
        code
        for el in _error_elements(root)
        if (code := el.get("code"))
    )


def extract_error_code(root: etree._Element | None) -> str | None:  # noqa: SLF001
    """Return the first OAI error code if the response contains &lt;error&gt;."""
    codes = extract_error_codes(root)
    return next(iter(codes), None)
