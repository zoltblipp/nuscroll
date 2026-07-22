"""Assemble ModuleReviews from planner entries, cache, and Disqus."""
from __future__ import annotations

from nuscrool import cache as cache_mod
from nuscrool import disqus
from nuscrool.disqus import DisqusError
from nuscrool.models import ModuleReviews, PlannerEntry, Review

_STALE_TTL = 10**9  # accept any cached age as fallback on fetch failure


def build_module_reviews(
    entries: list[PlannerEntry],
    titles: dict[str, str],
    api_key: str,
    *,
    ttl_seconds: int = 86400,
    now: float,
    force: bool = False,
    fetch=disqus.fetch_reviews,
    read_cache=cache_mod.read_cache,
    write_cache=cache_mod.write_cache,
    progress=None,
) -> list[ModuleReviews]:
    results: list[ModuleReviews] = []
    total = len(entries)
    for index, entry in enumerate(entries):
        if progress:
            progress(index, total, entry.module_code)
        code = entry.module_code
        title = titles.get(code, "")

        if not force:
            cached = read_cache(code, ttl_seconds, now)
            if cached is not None:
                results.append(ModuleReviews(code, title, entry.label, cached))
                continue

        try:
            reviews: list[Review] = fetch(code, api_key)
            write_cache(code, reviews, now)
            results.append(ModuleReviews(code, title, entry.label, reviews))
        except (DisqusError, OSError) as exc:
            fallback = read_cache(code, _STALE_TTL, now)
            results.append(
                ModuleReviews(
                    code, title, entry.label,
                    fallback or [],
                    error=str(exc),
                )
            )
    return results
