"""Central logging setup so errors show up clearly in uvicorn / container logs."""

from __future__ import annotations

import logging
import os
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(*, logger_name: str = "benson") -> logging.Logger:
    """Configure the app logger.

    Respect ``LOG_LEVEL`` (default ``INFO``). If the root logger has no handlers yet,
    attach a stderr ``StreamHandler`` so messages always appear alongside uvicorn.
    """
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    if not root.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATEFMT))
        root.addHandler(handler)
        root.setLevel(level)

    log = logging.getLogger(logger_name)
    log.setLevel(level)
    log.propagate = True
    return log
