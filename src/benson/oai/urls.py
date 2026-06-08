"""Build OAI request URLs from base endpoint."""

from __future__ import annotations


def append_oai_query(endpoint: str, query_part: str) -> str:
    """Append OAI query tokens; *query_part* may look like '?verb=X' or 'verb=X'.

    *endpoint* is the OAI base URL (typically without a trailing ``?``).
    """
    ep = endpoint.rstrip().rstrip("?&")
    q = query_part.lstrip()
    while q.startswith("?"):
        q = q[1:]
    q = q.lstrip("&")
    sep = "&" if "?" in ep else "?"
    return ep + sep + q
