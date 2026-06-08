"""Emit OAI-PMH ListRecords XML from publisher registry records."""

from __future__ import annotations

from lxml import etree

from benson.service.rofr_lists import PublisherRegistry

OAI_NS = "http://www.openarchives.org/OAI/2.0/"
RI_NS = "http://www.ivoa.net/xml/RegistryInterface/v1.0"
VG_NS = "http://www.ivoa.net/xml/VORegistry/v1.0"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

REGISTRY_STD = "ivo://ivoa.net/std/registry"


def publishers_to_list_records_xml(records: list[PublisherRegistry]) -> bytes:
    """Build an OAI-PMH ListRecords document for RofR harvesters."""
    root = etree.Element(
        f"{{{OAI_NS}}}OAI-PMH",
        nsmap={"oai": OAI_NS},
    )
    list_records = etree.SubElement(root, f"{{{OAI_NS}}}ListRecords")
    for rec in records:
        oai_rec = etree.SubElement(list_records, f"{{{OAI_NS}}}record")
        header = etree.SubElement(oai_rec, f"{{{OAI_NS}}}header")
        ident = etree.SubElement(header, f"{{{OAI_NS}}}identifier")
        ident.text = rec.oai_identifier
        metadata = etree.SubElement(oai_rec, f"{{{OAI_NS}}}metadata")
        resource = etree.SubElement(
            metadata,
            f"{{{RI_NS}}}Resource",
            nsmap={
                "ri": RI_NS,
                "vg": VG_NS,
                "xsi": XSI_NS,
            },
            attrib={f"{{{XSI_NS}}}type": "vg:Registry"},
        )
        title_el = etree.SubElement(resource, f"{{{RI_NS}}}title")
        title_el.text = rec.title
        if rec.harvest_access_url:
            cap = etree.SubElement(
                resource,
                f"{{{RI_NS}}}capability",
                attrib={
                    "standardID": REGISTRY_STD,
                    f"{{{XSI_NS}}}type": "vg:Harvest",
                },
            )
            iface = etree.SubElement(
                cap,
                f"{{{RI_NS}}}interface",
                attrib={f"{{{XSI_NS}}}type": "vg:OAIHTTP"},
            )
            url_el = etree.SubElement(iface, f"{{{RI_NS}}}accessURL")
            url_el.text = rec.harvest_access_url
    return etree.tostring(
        root,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )
