"""Tests for OAI endpoint URL construction."""

from benson.oai.urls import append_oai_query


def test_append_to_plain_oai_url() -> None:
    url = append_oai_query("https://registry.example/oai", "verb=Identify")
    assert url == "https://registry.example/oai?verb=Identify"


def test_append_strips_leading_question_mark_from_query_part() -> None:
    url = append_oai_query("https://registry.example/oai", "?verb=Identify")
    assert url == "https://registry.example/oai?verb=Identify"


def test_append_strips_trailing_question_mark_from_endpoint() -> None:
    url = append_oai_query("https://registry.example/oai?", "verb=Identify")
    assert url == "https://registry.example/oai?verb=Identify"


def test_append_to_endpoint_with_existing_query_string() -> None:
    url = append_oai_query("https://registry.example/oai?foo=bar", "verb=Identify")
    assert url == "https://registry.example/oai?foo=bar&verb=Identify"
    assert "&verb=Identify" in url
    assert "?verb=Identify" not in url


def test_append_strips_trailing_ampersand_from_endpoint() -> None:
    url = append_oai_query(
        "https://registry.example/oai?runid=abc&",
        "verb=ListRecords&metadataPrefix=ivo_vor",
    )
    assert url == "https://registry.example/oai?runid=abc&verb=ListRecords&metadataPrefix=ivo_vor"


def test_append_strips_leading_ampersand_from_query_part() -> None:
    url = append_oai_query("https://registry.example/oai", "&verb=Identify")
    assert url == "https://registry.example/oai?verb=Identify"
