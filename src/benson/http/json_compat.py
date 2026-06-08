"""JSON helpers for legacy-compatible responses."""

from __future__ import annotations

import json


def parity_dumps(payload: object) -> str:
    """JavaScript-ish object literals (single-quoted scalar strings).

    Mirrors ``docs/samples`` pseudo-JSON for ``StartSession`` / ``GetStatus``.
    """

    def _scalar(v: object) -> str:
        if isinstance(v, str):
            return "'" + v.replace("\\", "\\\\").replace("'", "\\'") + "'"
        if isinstance(v, bool):
            return "true" if v else "false"
        return json.dumps(v)

    def _walk(v: object) -> str:
        if isinstance(v, dict):
            parts = []
            for k, val in v.items():
                kk = str(k)
                parts.append(f"'{kk}': {_walk(val)}")
            return "{ " + ", ".join(parts) + " }"
        if isinstance(v, list):
            return "[ " + ", ".join(_walk(x) for x in v) + " ]"
        return _scalar(v)

    return _walk(payload)


def response_json(use_parity: bool, payload: object) -> str:
    if use_parity:
        return parity_dumps(payload)
    return json.dumps(payload)
