"""Invoke XSLT 1.0 stylesheets bundled under assets."""

from __future__ import annotations

from pathlib import Path

from lxml import etree


def transform(
    xsl_path: Path,
    source_doc: etree._ElementTree | etree._Element,
    *,
    params: dict[str, str] | None = None,
) -> etree._ElementTree:
    doc = (
        source_doc
        if isinstance(source_doc, etree._ElementTree)
        else etree.ElementTree(source_doc)
    )
    tpl = etree.XSLT(etree.parse(str(xsl_path)))
    kw = {k.replace(":", "_"): etree.XSLT.strparam(v) for k, v in (params or {}).items()}
    return tpl(doc, **kw)
