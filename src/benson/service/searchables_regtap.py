"""Full searchable registries: RegTAP sync (parity with listSearchables.py.in) and optional CSV cache."""

from __future__ import annotations

import csv
import logging
import time
from io import StringIO
from pathlib import Path

import httpx

from benson.config import Settings
from benson.service.rofr_lists import SearchableRegistry

logger = logging.getLogger("benson.service.searchables_regtap")

# Parity baseline: same SELECT as rofr.ivoa.net listSearchables.py.in
DEFAULT_SEARCHABLES_ADQL = (
    "select distinct r.ivoid, r.res_type, r.res_title, r.reference_url, c.ivoid, c.cap_type, "
    "c.standard_id, i.intf_type, i.url_use, i.access_url from rr.capability c, rr.resource r, "
    "rr.interface i where c.ivoid = r.ivoid and c.ivoid = i.ivoid and "
    "(c.cap_type like '%search%' or (c.cap_type like '%capability%' and c.standard_id like '%ivoa.net/std/tap%' "
    "and r.ivoid != 'ivo://archive.stsci.edu/nvoregistry')) and "
    "(i.intf_type like '%paramhttp%' or (i.intf_type like '%webservice%' and i.url_use = 'full')) "
    "and r.res_type = 'vg:registry'"
)


def parse_searchables_regtap_csv(text: str) -> list[SearchableRegistry]:
    """Map RegTAP CSV rows to SearchableRegistry (legacy column indices 0,2,3,7,9)."""
    reader = csv.reader(StringIO(text))
    rows = list(reader)
    if len(rows) < 2:
        return []
    out: list[SearchableRegistry] = []
    for fields in rows[1:]:
        if len(fields) != 10:
            continue
        ivoid = fields[0].strip()
        title = fields[2].strip() or "Registry"
        href = fields[3].strip() or None
        intf = fields[7].strip()
        access_url = fields[9].strip()
        if intf.startswith("vs:paramhttp"):
            endpoint_label = "RegTAP service endpoint"
        else:
            endpoint_label = "Search service endpoint"
        fields_map = {"IVOA Identifier": ivoid, endpoint_label: access_url}
        out.append(SearchableRegistry(title=title, href=href or None, fields=fields_map))
    return out


def _cache_path(settings: Settings) -> Path | None:
    if settings.searchables_cache_file is not None:
        return settings.searchables_cache_file
    if settings.searchables_cache_dir is not None:
        d = settings.searchables_cache_dir
        if not d.is_dir():
            return None
        csvs = list(d.glob("*.csv"))
        if not csvs:
            return None
        return max(csvs, key=lambda p: p.stat().st_mtime)
    return None


def _cache_is_fresh(path: Path, settings: Settings) -> bool:
    if settings.searchables_cache_max_age_sec is None:
        return True
    age = time.time() - path.stat().st_mtime
    return age <= settings.searchables_cache_max_age_sec


def _read_cache_if_usable(settings: Settings) -> list[SearchableRegistry] | None:
    path = _cache_path(settings)
    if path is None or not path.is_file() or path.stat().st_size == 0:
        return None
    if not _cache_is_fresh(path, settings):
        logger.info("searchables cache stale, using RegTAP: %s", path)
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        logger.warning("searchables cache read failed: %s", e)
        return None
    return parse_searchables_regtap_csv(text)


async def fetch_searchables_from_regtap(
    client: httpx.AsyncClient, settings: Settings, *, timeout_sec: float
) -> list[SearchableRegistry]:
    query = settings.searchables_adql.strip() or DEFAULT_SEARCHABLES_ADQL
    payload = {
        "LANG": "ADQL",
        "responseformat": "csv",
        "param_format": "csv",
        "QUERY": query,
    }
    r = await client.post(
        settings.searchables_regtap_sync_url,
        data=payload,
        timeout=timeout_sec,
    )
    r.raise_for_status()
    return parse_searchables_regtap_csv(r.text)


async def load_searchables(
    client: httpx.AsyncClient, settings: Settings, *, timeout_sec: float
) -> list[SearchableRegistry]:
    cached = _read_cache_if_usable(settings)
    if cached is not None:
        return cached
    return await fetch_searchables_from_regtap(client, settings, timeout_sec=timeout_sec)
