"""Namespace URI to local XSD filename (regvalidate-functional-contract §5)."""

from __future__ import annotations

from pathlib import Path

# Mirrors docs/regvalidate-functional-contract.md §5
NAMESPACE_SCHEMA_FILES: dict[str, str] = {
    "http://oai.dlib.vt.edu/OAI/metadata/toolkit": "OAItoolkit.xsd",
    "http://www.w3.org/XML/1998/namespace": "xml.xsd",
    "http://purl.org/dc/elements/1.1/": "simpledc20021212.xsd",
    "http://www.openarchives.org/OAI/2.0/oai_dc/": "oai_dc.xsd",
    "http://www.openarchives.org/OAI/2.0/": "OAI-v2.xsd",
    "http://www.w3.org/1999/xlink": "xlink.xsd",
    "http://www.ivoa.net/xml/STC/stc-v1.30.xsd": "stc-v1.xsd",
    "http://www.ivoa.net/xml/VOResource/v1.0": "VOResource-v1.xsd",
    "http://www.ivoa.net/xml/RegistryInterface/v1.0": "RegistryInterface-v1.xsd",
    "http://www.ivoa.net/xml/VODataService/v1.1": "VODataService-v1.xsd",
    "http://www.ivoa.net/xml/VORegistry/v1.0": "VORegistry-v1.xsd",
    "http://www.ivoa.net/xml/SIA/v1.1": "SIA-v1.xsd",
    "http://www.ivoa.net/xml/SSA/v1.1": "SSA-v1.xsd",
    "http://www.ivoa.net/xml/ConeSearch/v1.0": "ConeSearch-v1.xsd",
    "http://www.ivoa.net/xml/StandardsRegExt/v1.0": "StandardsRegExt-v1.xsd",
    "http://www.ivoa.net/xml/TAPRegExt/v1.0": "TAPRegExt-v1.xsd",
    "http://www.ivoa.net/xml/VOSIAvailability/v1.0": "VOSIAvailability-v1.xsd",
    "http://www.ivoa.net/xml/VOSICapabilities/v1.0": "VOSICapabilities-v1.xsd",
    "http://www.ivoa.net/xml/VOSITables/v1.0": "VOSITables-v1.xsd",
}


def resolve_schema_path(namespace_or_none: str, schema_root: Path) -> Path | None:
    if not namespace_or_none:
        return None
    fname = NAMESPACE_SCHEMA_FILES.get(namespace_or_none.strip())
    if not fname:
        return None
    p = schema_root / fname
    return p if p.is_file() else None


def oai_pmh_schema_path(schema_root: Path) -> Path:
    return schema_root / "OAI-v2.xsd"
