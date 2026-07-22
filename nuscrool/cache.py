"""Per-module review cache with TTL under ~/.nuscrool/cache/."""
from __future__ import annotations

import json
from dataclasses import asdict

from nuscrool.models import Review
from nuscrool.paths import nuscrool_home


def _cache_dir():
    d = nuscrool_home() / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_path(module_code: str):
    return _cache_dir() / f"{module_code}.json"


def read_cache(module_code: str, ttl_seconds: int, now: float) -> list[Review] | None:
    path = _cache_path(module_code)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    fetched_at = data.get("fetchedAt", 0)
    if now - fetched_at > ttl_seconds:
        return None
    try:
        return [Review(**post) for post in data.get("posts", [])]
    except (TypeError, KeyError):
        return None


def write_cache(module_code: str, reviews: list[Review], now: float) -> None:
    payload = {"fetchedAt": now, "posts": [asdict(r) for r in reviews]}
    _cache_path(module_code).write_text(json.dumps(payload, indent=2))
