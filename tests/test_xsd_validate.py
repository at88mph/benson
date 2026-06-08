"""XSD validation with bundled IVOA schema catalog."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

_repo = Path(__file__).resolve().parents[1]
os.environ.setdefault("SCHEMA_ROOT", str(_repo / "assets" / "schemas"))

from benson.xml import xsd_validate  # noqa: E402

_SCHEMA_ROOT = Path(os.environ["SCHEMA_ROOT"])


@pytest.fixture
def cadc_identify_bytes() -> bytes:
    return (_repo / "tests" / "fixtures" / "cadc_identify.xml").read_bytes()


def test_cadc_identify_envelope_passes_builtin_catalog(cadc_identify_bytes: bytes) -> None:
    errors = xsd_validate.validate_oai_response_envelope(cadc_identify_bytes, _SCHEMA_ROOT)
    assert errors == [], errors


def test_cadc_identify_resource_fragment_passes_ivoa_bundle(cadc_identify_bytes: bytes) -> None:
    from lxml import etree

    root = etree.fromstring(cadc_identify_bytes)
    ri_ns = "http://www.ivoa.net/xml/RegistryInterface/v1.0"
    resource = root.find(f".//{{{ri_ns}}}Resource")
    assert resource is not None
    errors = xsd_validate.validate_element_tree(resource, _SCHEMA_ROOT)
    assert errors == [], errors
