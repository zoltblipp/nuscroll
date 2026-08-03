"""Assemble ModuleReviews from planner entries, cache, and Disqus."""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from nuscroll import cache as cache_mod
from nuscroll import disqus
from nuscroll.disqus import DisqusError
from nuscroll.models import ModuleReviews, PlannerEntry, Review

_STALE_TTL = 10**9  # accept any cached age as fallback on fetch failure
_MAX_WORKERS = 8  # bounded so we don't hammer the Disqus API with 40+ requests at once


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
    total = len(entries)
    results: list[ModuleReviews | None] = [None] * total
    to_fetch: list[int] = []

    # Cache reads are cheap local disk hits, so resolve them up front and
    # only hand the genuinely network-bound modules to the thread pool.
    for i, entry in enumerate(entries):
        code = entry.module_code
        title = titles.get(code, "")
        cached = None if force else read_cache(code, ttl_seconds, now)
        if cached is not None:
            results[i] = ModuleReviews(code, title, entry.label, cached)
        else:
            to_fetch.append(i)

    def _fetch_one(i: int) -> ModuleReviews:
        entry = entries[i]
        code = entry.module_code
        title = titles.get(code, "")
        try:
            reviews: list[Review] = fetch(code, api_key)
            write_cache(code, reviews, now)
            return ModuleReviews(code, title, entry.label, reviews)
        except (DisqusError, OSError, json.JSONDecodeError) as exc:
            try:
                fallback = read_cache(code, _STALE_TTL, now)
            except OSError:
                fallback = None
            return ModuleReviews(code, title, entry.label, fallback or [], error=str(exc))

    if to_fetch:
        # Disqus calls are I/O-bound (network round trips, some modules
        # paginating over hundreds of posts), so fetching them concurrently
        # cuts wall-clock time roughly by the worker count instead of
        # summing every module's latency one at a time.
        with ThreadPoolExecutor(max_workers=min(_MAX_WORKERS, len(to_fetch))) as pool:
            future_to_index = {pool.submit(_fetch_one, i): i for i in to_fetch}
            for completed, future in enumerate(as_completed(future_to_index)):
                i = future_to_index[future]
                results[i] = future.result()
                if progress:
                    progress(completed, len(to_fetch), entries[i].module_code)

    return results
