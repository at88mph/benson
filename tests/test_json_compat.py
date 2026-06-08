"""Parity pseudo-JSON encoding."""

from benson.http.json_compat import parity_dumps


def test_parity_nested_dict() -> None:
    s = parity_dumps({"status": "ready"})
    assert "'status'" in s
    assert "'ready'" in s


def test_parity_array() -> None:
    s = parity_dumps([{"id": "13", "message": "m"}])
    assert "'id'" in s
