"""Reverse-proxy support for scheme and host used by ``request.url`` / template ``url_for``."""

from __future__ import annotations

from typing import Any

from starlette.types import ASGIApp, Receive, Scope, Send


def _replace_host_header(headers: list[tuple[bytes, bytes]], host: str) -> list[tuple[bytes, bytes]]:
    encoded = host.encode("latin1")
    out: list[tuple[bytes, bytes]] = []
    replaced = False
    for key, value in headers:
        if key == b"host":
            out.append((b"host", encoded))
            replaced = True
        else:
            out.append((key, value))
    if not replaced:
        out.append((b"host", encoded))
    return out


class ForwardedHostMiddleware:
    """Map ``X-Forwarded-Host`` onto the ASGI ``Host`` header Starlette uses for URLs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            headers = dict(scope.get("headers", []))
            forwarded_host = headers.get(b"x-forwarded-host")
            if forwarded_host:
                host = forwarded_host.decode("latin1").split(",")[0].strip()
                if host:
                    scope["headers"] = _replace_host_header(list(scope["headers"]), host)
        await self.app(scope, receive, send)


def wrap_proxy_middleware(app: ASGIApp, *, trusted_hosts: str, enabled: bool) -> Any:
    if not enabled:
        return app
    from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

    app = ProxyHeadersMiddleware(app, trusted_hosts=trusted_hosts)
    return ForwardedHostMiddleware(app)
