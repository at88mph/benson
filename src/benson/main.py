"""CLI entry point for running the Benson HTTP server."""

from __future__ import annotations

import argparse
import os


def _dev_mode_enabled() -> bool:
    return os.environ.get("BENSON_DEV", "").lower() in ("1", "true", "yes")


def _apply_proxy_settings(*, enabled: bool, forwarded_allow_ips: str | None) -> None:
    os.environ["BENSON_PROXY_HEADERS"] = "true" if enabled else "false"
    if forwarded_allow_ips is not None:
        os.environ["FORWARDED_ALLOW_IPS"] = forwarded_allow_ips


def main() -> None:
    import uvicorn

    parser = argparse.ArgumentParser(description="Run the Benson registry validator.")
    parser.add_argument(
        "--reload",
        "-r",
        action="store_true",
        help="Enable auto-reload when source or asset files change (development)",
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--proxy-headers",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Trust X-Forwarded-Proto and X-Forwarded-Host from reverse proxies "
            "(default: enabled). Applied in the app so url_for and request.url are correct."
        ),
    )
    parser.add_argument(
        "--forwarded-allow-ips",
        default=None,
        metavar="IPS",
        help=(
            "Comma-separated IPs/networks allowed to set forwarded headers "
            "(default: FORWARDED_ALLOW_IPS env or '*'). Passed to uvicorn when --proxy-headers is on."
        ),
    )
    args = parser.parse_args()

    from benson.config import project_root

    forwarded = args.forwarded_allow_ips
    if forwarded is None:
        forwarded = os.environ.get("FORWARDED_ALLOW_IPS", "*")

    _apply_proxy_settings(enabled=args.proxy_headers, forwarded_allow_ips=forwarded)

    reload = args.reload or _dev_mode_enabled()
    root = project_root()
    reload_dirs = [str(root / "src"), str(root / "assets")] if reload else None

    # Proxy handling is applied in create_app via ProxyHeadersMiddleware so
    # template url_for() sees X-Forwarded-Proto/Host. Avoid enabling uvicorn's
    # second wrapper (would double-apply). For raw ``uvicorn --factory``, pass
    # ``--proxy-headers`` only if you disable BENSON_PROXY_HEADERS on the app.
    uvicorn.run(
        "benson.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=reload,
        reload_dirs=reload_dirs,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
