"""Resolve bundled XSD imports and compose schema sets for OAI / IVOA validation."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from lxml import etree

from benson.xml.catalog import NAMESPACE_SCHEMA_FILES

# Common schemaLocation URLs in IVOA XSD imports (not all are namespace URIs).
_IMPORT_URL_TO_FILE: dict[str, str] = {
    "http://www.ivoa.net/xml/VOResource/v1.0": "VOResource-v1.xsd",
    "http://www.ivoa.net/xml/VOResource/VOResource-v1.0.xsd": "VOResource-v1.xsd",
    "https://www.ivoa.net/xml/VOResource/v1.0": "VOResource-v1.xsd",
    "http://www.ivoa.net/xml/VORegistry/v1.0": "VORegistry-v1.xsd",
    "https://www.ivoa.net/xml/VORegistry/v1.0": "VORegistry-v1.xsd",
    "http://www.ivoa.net/xml/VODataService/v1.1": "VODataService-v1.xsd",
    "https://www.ivoa.net/xml/VODataService/v1.1": "VODataService-v1.xsd",
    "http://www.ivoa.net/xml/RegistryInterface/v1.0": "RegistryInterface-v1.xsd",
    "http://www.ivoa.net/xml/STC/stc-v1.30.xsd": "stc-v1.xsd",
    "http://hea-www.harvard.edu/~arots/nvometa/v1.30/stc-v1.30.xsd": "stc-v1.xsd",
    "http://www.ivoa.net/xml/Xlink/xlink.xsd": "xlink.xsd",
    "http://www.w3.org/1999/xlink": "xlink.xsd",
    "http://purl.org/dc/elements/1.1/": "simpledc20021212.xsd",
    "http://dublincore.org/schemas/xmls/simpledc20021212.xsd": "simpledc20021212.xsd",
    "http://www.openarchives.org/OAI/2.0/oai_dc/": "oai_dc.xsd",
    "http://www.openarchives.org/OAI/2.0/": "OAI-v2.xsd",
    "http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd": "OAI-v2.xsd",
    "https://www.openarchives.org/OAI/2.0/OAI-PMH.xsd": "OAI-v2.xsd",
    "http://www.w3.org/XML/1998/namespace": "xml.xsd",
    "http://www.w3.org/2001/03/xml.xsd": "xml.xsd",
}

RI_NS = "http://www.ivoa.net/xml/RegistryInterface/v1.0"
IVOA_BUNDLE = "benson-ivoa-bundle.xsd"
OAI_BUNDLE = "benson-oai-bundle.xsd"


class BundledSchemaResolver(etree.Resolver):
    """Map remote schemaLocation URLs to files under SCHEMA_ROOT."""

    def __init__(self, schema_root: Path) -> None:
        self.schema_root = schema_root.resolve()
        self._url_map = dict(_IMPORT_URL_TO_FILE)
        for _ns, fname in NAMESPACE_SCHEMA_FILES.items():
            self._url_map.setdefault(_ns.rstrip("/"), fname)
            self._url_map.setdefault(_ns, fname)

    def resolve(self, system_url: str, _public_id: str, context) -> object | None:  # noqa: ANN001
        url = (system_url or "").strip()
        if not url:
            return None
        candidates = [url, url.rstrip("/")]
        if url.startswith("file:"):
            candidates.append(Path(url[5:]).name)
        for key in candidates:
            fname = self._url_map.get(key)
            if fname:
                path = self.schema_root / fname
                if path.is_file():
                    return self.resolve_filename(str(path), context)
        # basename fallback (e.g. VOResource-v1.0.xsd)
        base = Path(url).name
        if base:
            path = self.schema_root / base
            if path.is_file():
                return self.resolve_filename(str(path), context)
        return None


def _parser_with_resolver(schema_root: Path) -> etree.XMLParser:
    parser = etree.XMLParser()
    parser.resolvers.add(BundledSchemaResolver(schema_root))
    return parser


@lru_cache(maxsize=8)
def ivoa_bundle_schema(schema_root_str: str) -> etree.XMLSchema:
    """Schema set for RI Resource payloads (RegistryInterface + VORegistry extensions)."""
    root = Path(schema_root_str)
    path = root / IVOA_BUNDLE
    parser = _parser_with_resolver(root)
    return etree.XMLSchema(etree.parse(str(path), parser))


@lru_cache(maxsize=8)
def oai_bundle_schema(schema_root_str: str) -> etree.XMLSchema:
    """Schema set for OAI-PMH envelope validation (OAI + oai_dc for description stubs)."""
    root = Path(schema_root_str)
    path = root / OAI_BUNDLE
    parser = _parser_with_resolver(root)
    return etree.XMLSchema(etree.parse(str(path), parser))


@lru_cache(maxsize=32)
def namespace_schema(schema_root_str: str, namespace: str) -> etree.XMLSchema | None:
    """Single-namespace schema from the catalog, with bundled import resolution."""
    root = Path(schema_root_str)
    fname = NAMESPACE_SCHEMA_FILES.get(namespace)
    if not fname:
        for uri, fn in NAMESPACE_SCHEMA_FILES.items():
            if uri.rstrip("/") == namespace.rstrip("/"):
                fname = fn
                break
    if not fname:
        return None
    path = root / fname
    if not path.is_file():
        return None
    parser = _parser_with_resolver(root)
    return etree.XMLSchema(etree.parse(str(path), parser))
