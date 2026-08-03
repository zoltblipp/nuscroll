"""Fetch NUS module titles from the NUSMods metadata API (cached)."""
from __future__ import annotations

import json

from nuscroll import disqus
from nuscroll.paths import nuscroll_home

_BASE = "https://api.nusmods.com/v2"


def acad_year_from_min(min_year: str) -> str:
    """'2026/2027' -> '2026-2027'."""
    return min_year.replace("/", "-")


def _cache_path(acad_year: str):
    d = nuscroll_home() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"_modulelist_{acad_year}.json"


def _read_cache(acad_year: str, ttl_seconds: int, now: float) -> dict[str, str] | None:
    path = _cache_path(acad_year)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    if now - data.get("fetchedAt", 0) > ttl_seconds:
        return None
    return data.get("titles", {})


def fetch_titles(
    acad_year: str,
    *,
    ttl_seconds: int = 86400,
    now: float,
    fetch_json=disqus._default_fetch_json,
) -> dict[str, str]:
    cached = _read_cache(acad_year, ttl_seconds, now)
    if cached is not None:
        return cached

    url = f"{_BASE}/{acad_year}/moduleList.json"
    try:
        modules = fetch_json(url)
        titles = {m["moduleCode"]: m.get("title", "") for m in modules}
        _cache_path(acad_year).write_text(
            json.dumps({"fetchedAt": now, "titles": titles})
        )
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return {}
    return titles
