"""Map ri:Resource metadata to OAI Dublin Core."""

from __future__ import annotations

from lxml import etree

OAI_DC_NS = "http://www.openarchives.org/OAI/2.0/oai_dc/"
DC_NS = "http://purl.org/dc/elements/1.1/"


def _find_direct(parent: etree._Element, local_name: str) -> etree._Element | None:  # noqa: SLF001
    for el in parent:
        tag = el.tag
        if isinstance(tag, str) and tag.rsplit("}", 1)[-1] == local_name:
            return el
    return None


def _text(parent: etree._Element, tag: str) -> str | None:  # noqa: SLF001
    el = _find_direct(parent, tag)
    if el is not None and el.text and el.text.strip():
        return el.text.strip()
    return None


def _local_tag(el: etree._Element) -> str:  # noqa: SLF001
    tag = el.tag
    if isinstance(tag, str):
        return tag.rsplit("}", 1)[-1]
    return ""


def resource_to_oai_dc(metadata: etree._Element) -> etree._Element:  # noqa: SLF001
    """Wrap a ``ri:Resource`` in ``oai_dc:dc`` for ``metadataPrefix=oai_dc``."""
    wrapper = etree.Element(
        f"{{{OAI_DC_NS}}}dc",
        nsmap={"oai_dc": OAI_DC_NS, "dc": DC_NS},
    )
    title = _text(metadata, "title")
    if title:
        el = etree.SubElement(wrapper, f"{{{DC_NS}}}title")
        el.text = title
    ident = _text(metadata, "identifier")
    if ident:
        el = etree.SubElement(wrapper, f"{{{DC_NS}}}identifier")
        el.text = ident
    content = _find_direct(metadata, "content")
    if content is not None:
        desc = _text(content, "description")
        if desc:
            el = etree.SubElement(wrapper, f"{{{DC_NS}}}description")
            el.text = desc
    curation = _find_direct(metadata, "curation")
    if curation is not None:
        for date_el in curation:
            if _local_tag(date_el) == "date" and date_el.text and date_el.text.strip():
                el = etree.SubElement(wrapper, f"{{{DC_NS}}}date")
                el.text = date_el.text.strip()
                break
    updated = metadata.get("updated")
    if updated and not wrapper.findall(f"{{{DC_NS}}}date"):
        el = etree.SubElement(wrapper, f"{{{DC_NS}}}date")
        el.text = updated.strip()
    return wrapper
