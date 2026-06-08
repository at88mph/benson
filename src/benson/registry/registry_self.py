"""Runtime-generated vg:Registry and vg:Authority records for the /oai endpoint."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from benson.config import Settings
from benson.oai.dates import normalize_datestamp

RI_NS = "http://www.ivoa.net/xml/RegistryInterface/v1.0"
VG_NS = "http://www.ivoa.net/xml/VORegistry/v1.0"
VR_NS = "http://www.ivoa.net/xml/VOResource/v1.0"
VS_NS = "http://www.ivoa.net/xml/VODataService/v1.1"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

REGISTRY_STD = "ivo://ivoa.net/std/Registry"
IVOA_PUBLISHER_ID = "ivo://ivoa.net/IVOA"
IVOA_ORG_ID = "ivo://ivoa.net/IVOA"

REGISTRY_CREATED = "2006-07-01T09:00:00"
REGISTRY_UPDATED = "2025-04-17T17:28:00"
AUTHORITY_CREATED = "2006-07-01T09:00:00"
IVOA_ORG_CREATED = "2000-01-01T09:00:00"

ROFR_DESCRIPTION = (
    "This is a special publishing registry that describes "
    "resources that represent important infrastructure "
    "components to the VO registry framework.  A primary purpose "
    "is to provide a registry to discover other publishing "
    "registries.  A registry that wants to harvest all records "
    "known to the VO can first harvest from this registry a list "
    "of all known publishing registries (via the IVOA Registry "
    "Interface for harvesting with set=ivoa_publishers).  An "
    "interactive interface allows publishing registry providers "
    "to check their interfaces and make their registries known to "
    "the framework.  This registry also describes standard "
    "protocols recognized by the IVOA."
)

IVOA_ORG_DESCRIPTION = (
    "The International Virtual Observatory Alliance (IVOA) was "
    "formed in June 2002 with a mission to facilitate the "
    "international coordination and collaboration necessary for the "
    "development and deployment of the tools, systems and "
    "organizational structures necessary to enable the "
    "international utilization of astronomical archives as an "
    "integrated and interoperating virtual observatory."
)

_XML_PARSER = etree.XMLParser(no_network=True, resolve_entities=False)


def _find_direct(root: etree._Element, local_name: str) -> etree._Element | None:  # noqa: SLF001
    for el in root:
        tag = el.tag
        if not isinstance(tag, str):
            continue
        if tag.rsplit("}", 1)[-1] == local_name:
            return el
    return None


def _load_resource_file(path: Path) -> etree._Element:
    root = etree.parse(str(path), _XML_PARSER).getroot()
    return etree.fromstring(etree.tostring(root, encoding="UTF-8"), parser=_XML_PARSER)


def _authority_asset_path(settings: Settings) -> Path:
    return settings.standards_dir.parent / "authority" / "ivoa.xml"


def build_registry_resource(base_url: str, settings: Settings) -> etree._Element:
    """Build the vg:Registry ri:Resource for Identify and ListRecords."""
    site_root = base_url.rstrip("/").rsplit("/oai", 1)[0] or base_url
    resource = etree.Element(
        f"{{{RI_NS}}}Resource",
        nsmap={
            "ri": RI_NS,
            "vg": VG_NS,
            "vr": VR_NS,
            "vs": VS_NS,
            "xsi": XSI_NS,
        },
        attrib={
            f"{{{XSI_NS}}}type": "vg:Registry",
            "status": "active",
            "created": REGISTRY_CREATED,
            "updated": REGISTRY_UPDATED,
        },
    )
    title_el = etree.SubElement(resource, "title")
    title_el.text = settings.oai_repository_name
    short_el = etree.SubElement(resource, "shortName")
    short_el.text = "RofR"
    ident_el = etree.SubElement(resource, "identifier")
    ident_el.text = settings.oai_registry_identifier

    curation = etree.SubElement(resource, "curation")
    pub = etree.SubElement(curation, "publisher", attrib={"ivo-id": IVOA_PUBLISHER_ID})
    pub.text = "International Virtual Observatory Alliance"
    creator = etree.SubElement(curation, "creator")
    name = etree.SubElement(creator, "name")
    name.text = "Raymond Plante"
    logo = etree.SubElement(creator, "logo")
    logo.text = "http://www.ivoa.net/icons/ivoa_logo_small.jpg"
    created = etree.SubElement(curation, "date", attrib={"role": "created"})
    created.text = "2007-07-01"
    updated = etree.SubElement(curation, "date", attrib={"role": "updated"})
    updated.text = "2025-04-17"
    version = etree.SubElement(curation, "version")
    version.text = "1.1"
    contact = etree.SubElement(curation, "contact")
    cname = etree.SubElement(contact, "name")
    cname.text = "IVOA Resource Registry Working Group"
    email = etree.SubElement(contact, "email")
    email.text = "support@canfar.net"

    content = etree.SubElement(resource, "content")
    subj = etree.SubElement(content, "subject")
    subj.text = "virtual observatory"
    desc = etree.SubElement(content, "description")
    desc.text = ROFR_DESCRIPTION
    ref = etree.SubElement(content, "referenceURL")
    ref.text = f"{site_root}/" if site_root else site_root
    typ = etree.SubElement(content, "type")
    typ.text = "Registry"

    cap = etree.SubElement(
        resource,
        "capability",
        attrib={
            "standardID": REGISTRY_STD,
            f"{{{XSI_NS}}}type": "vg:Harvest",
        },
    )
    iface = etree.SubElement(
        cap,
        "interface",
        attrib={
            f"{{{XSI_NS}}}type": "vg:OAIHTTP",
            "role": "std",
            "version": "1.0",
        },
    )
    url_el = etree.SubElement(iface, "accessURL")
    url_el.text = base_url.rstrip("?&")
    max_rec = etree.SubElement(cap, "maxRecords")
    max_rec.text = "0"

    full_el = etree.SubElement(resource, "full")
    full_el.text = "false"
    auth_el = etree.SubElement(resource, "managedAuthority")
    auth_el.text = settings.oai_managed_authority
    return resource


def build_authority_resource(settings: Settings, base_url: str) -> etree._Element:
    """Load the vg:Authority ri:Resource for the managed naming authority."""
    return _load_resource_file(_authority_asset_path(settings))


def build_ivoa_authority_resource() -> etree._Element:
    """Build the vr:Organisation ri:Resource for ivo://ivoa.net/IVOA."""
    resource = etree.Element(
        f"{{{RI_NS}}}Resource",
        nsmap={
            "ri": RI_NS,
            "vr": VR_NS,
            "xsi": XSI_NS,
        },
        attrib={
            f"{{{XSI_NS}}}type": "vr:Organisation",
            "status": "active",
            "created": IVOA_ORG_CREATED,
            "updated": IVOA_ORG_CREATED,
        },
    )
    title_el = etree.SubElement(resource, "title")
    title_el.text = "International Virtual Observatory Alliance"
    short_el = etree.SubElement(resource, "shortName")
    short_el.text = "IVOA"
    ident_el = etree.SubElement(resource, "identifier")
    ident_el.text = IVOA_ORG_ID

    curation = etree.SubElement(resource, "curation")
    pub = etree.SubElement(curation, "publisher")
    pub.text = "International Virtual Observatory Alliance"
    creator = etree.SubElement(curation, "creator")
    name = etree.SubElement(creator, "name")
    name.text = "VO community"
    logo = etree.SubElement(creator, "logo")
    logo.text = "http://www.ivoa.net/icons/ivoa_logo_small.jpg"
    date_el = etree.SubElement(curation, "date")
    date_el.text = "2002-06-01"
    contact = etree.SubElement(curation, "contact")
    cname = etree.SubElement(contact, "name")
    cname.text = "IVOA Executive Committee"
    email = etree.SubElement(contact, "email")
    email.text = "ivoa@ivoa.net"

    content = etree.SubElement(resource, "content")
    for subject in ("standards", "virtual observatory"):
        subj = etree.SubElement(content, "subject")
        subj.text = subject
    desc = etree.SubElement(content, "description")
    desc.text = IVOA_ORG_DESCRIPTION
    ref = etree.SubElement(content, "referenceURL")
    ref.text = "http://www.ivoa.net/"
    typ = etree.SubElement(content, "type")
    typ.text = "Organisation"
    return resource


def _record_tuple(
    ident: str,
    stamp: str,
    metadata: etree._Element,
) -> tuple[str, str, str, etree._Element]:
    return ident, normalize_datestamp(stamp), "active", metadata


def registry_record(settings: Settings, base_url: str) -> tuple[str, str, str, etree._Element]:
    """Return (identifier, datestamp, status, metadata) for the registry record."""
    el = build_registry_resource(base_url, settings)
    return _record_tuple(settings.oai_registry_identifier, REGISTRY_UPDATED, el)


def authority_record(settings: Settings, base_url: str) -> tuple[str, str, str, etree._Element]:
    """Return (identifier, datestamp, status, metadata) for the authority record."""
    el = build_authority_resource(settings, base_url)
    ident_el = _find_direct(el, "identifier")
    if ident_el is None or not (ident_el.text and ident_el.text.strip()):
        msg = f"Missing identifier in {_authority_asset_path(settings).name}"
        raise ValueError(msg)
    ident = ident_el.text.strip()
    updated = el.get("updated") or AUTHORITY_CREATED
    status = el.get("status") or "active"
    return ident, normalize_datestamp(updated), status, el


def ivoa_authority_record() -> tuple[str, str, str, etree._Element]:
    """Return (identifier, datestamp, status, metadata) for the IVOA organisation."""
    el = build_ivoa_authority_resource()
    return _record_tuple(IVOA_ORG_ID, IVOA_ORG_CREATED, el)
