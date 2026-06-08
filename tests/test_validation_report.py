"""Tests for validation report HTML rendering."""

from __future__ import annotations

from pathlib import Path

from lxml import etree

from benson.http.validation_report import render_validation_report

_repo = Path(__file__).resolve().parents[1]
_SAMPLE = _repo / "docs" / "samples" / "harvest-validater" / "02-validate-oai.xml"


def _tree(xml: str) -> etree._ElementTree:
    return etree.ElementTree(etree.fromstring(xml.encode()))


def test_render_merged_registry_validation() -> None:
    xml = """<RegistryValidation status="completed" nfail="2" nwarn="0" nrec="0">
      <OAIValidation baseURL="https://example/oai" showStatus="fail warn rec" testCount="1">
        <testQuery name="Identify" options="verb=Identify" role="oai">
          <test item="summary" status="fail">Not compliant</test>
        </testQuery>
      </OAIValidation>
      <HarvestValidation baseURL="https://example/oai" showStatus="fail warn rec">
        <testQuery name="ListSets" options="verb=ListSets" role="ListSets">
          <test item="RI3.1.1" status="pass">OK</test>
        </testQuery>
      </HarvestValidation>
    </RegistryValidation>"""
    html = render_validation_report(_tree(xml))
    assert "val-summary--fail" in html
    assert "1 failure" in html
    assert "val-jump" in html
    assert "Not compliant" in html
    assert "val-section" in html
    assert "OAI-PMH conformance" in html
    assert "IVOA harvest profile" in html
    assert "val-passed-group" in html
    assert "val-toolbar" in html


def test_render_all_passed() -> None:
    xml = """<RegistryValidation status="completed" nfail="0" nwarn="0" nrec="0">
      <HarvestValidation baseURL="https://example/oai" showStatus="fail warn rec">
        <testQuery name="Identify" options="verb=Identify" role="Identify">
          <test item="RI3.1.1" status="pass">OK</test>
        </testQuery>
      </HarvestValidation>
    </RegistryValidation>"""
    html = render_validation_report(_tree(xml))
    assert "val-summary--pass" in html
    assert "All checks passed" in html
    assert "1 passed check" in html


def test_render_sample_oai_xml() -> None:
    tree = etree.parse(str(_SAMPLE))
    html = render_validation_report(tree)
    assert "val-summary--fail" in html
    assert "val-jump" in html
    assert "badVerb" in html
    assert "Identify" in html
    assert 'href="#val-oai-' in html


def test_summary_counts_queries_not_individual_tests() -> None:
    xml = """<RegistryValidation status="completed" nfail="1" nwarn="0" nrec="0">
      <OAIValidation baseURL="https://example/oai" showStatus="fail warn rec" testCount="2">
        <testQuery name="Bad" options="?verb=Bad" role="oai">
          <test item="summary" status="fail">Not compliant</test>
          <test item="oai-1" status="fail">badVerb</test>
        </testQuery>
        <testQuery name="Good" options="?verb=Good" role="oai">
          <test item="RI3.1.1" status="pass">OK</test>
        </testQuery>
      </OAIValidation>
    </RegistryValidation>"""
    html = render_validation_report(_tree(xml))
    assert "1 failure" in html
    assert "1 passed" in html
    assert "Failures (1)" in html
    assert "Passed (1)" in html
    assert "All (2)" in html
    assert "1 failed" in html
    assert "1 passed" in html


def test_render_ignored_errors_note() -> None:
    xml = """<RegistryValidation status="completed" nfail="0" nwarn="0" nrec="0">
      <OAIValidation baseURL="https://example/oai" showStatus="fail warn rec" testCount="1">
        <testQuery name="ListRecords (illegal_resumptiontoken)"
                   options="?verb=ListRecords&amp;resumptionToken=junktoken"
                   role="oai"
                   ignoredErrors="badArgument">
          <test item="summary" status="pass">Operation must be compliant with OAI-PMH standard</test>
          <test item="compliant-response" status="pass"></test>
        </testQuery>
      </OAIValidation>
    </RegistryValidation>"""
    html = render_validation_report(_tree(xml))
    assert "val-ignored-note" in html
    assert "Ignored error code:" in html
    assert "badArgument" in html


def test_passed_checks_grouped_separately() -> None:
    xml = """<RegistryValidation status="completed" nfail="1" nwarn="0" nrec="0">
      <OAIValidation baseURL="https://example/oai" showStatus="fail warn rec" testCount="2">
        <testQuery name="Bad" options="?verb=Bad" role="oai">
          <test item="oai-1" status="fail">nope</test>
        </testQuery>
        <testQuery name="Good" options="?verb=Good" role="oai">
          <test item="summary" status="pass">OK</test>
        </testQuery>
      </OAIValidation>
    </RegistryValidation>"""
    html = render_validation_report(_tree(xml))
    assert 'id="val-oai-0-bad"' in html
    assert "val-passed-group" in html
    assert "1 passed check" in html
