import pytest

from nuscrool import loader
from nuscrool.disqus import DisqusError
from nuscrool.models import PlannerEntry, Review


def _entry(code, label="Y1S1"):
    return PlannerEntry(code, label, (0, 1, 1, code))


def test_uses_cache_when_fresh():
    def read_cache(code, ttl_seconds, now):
        return [Review("Cached", "2024", "hi", 0)]

    def fetch(code, key, **kw):
        raise AssertionError("should not fetch when cache is fresh")

    out = loader.build_module_reviews(
        [_entry("CS2100")], {"CS2100": "Comp Org"}, "KEY",
        now=1.0, read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
    )
    assert out[0].reviews[0].author == "Cached"
    assert out[0].title == "Comp Org"
    assert out[0].error is None


def test_fetches_and_writes_on_cache_miss():
    written = {}

    def read_cache(code, ttl_seconds, now):
        return None

    def fetch(code, key, **kw):
        return [Review("Net", "2024", "fresh", 1)]

    def write_cache(code, reviews, now):
        written[code] = reviews

    out = loader.build_module_reviews(
        [_entry("CS2100")], {}, "KEY",
        now=1.0, read_cache=read_cache, fetch=fetch, write_cache=write_cache,
    )
    assert out[0].reviews[0].message == "fresh"
    assert "CS2100" in written


def test_force_bypasses_fresh_cache():
    def read_cache(code, ttl_seconds, now):
        raise AssertionError("force should skip read_cache")

    def fetch(code, key, **kw):
        return [Review("Net", "2024", "forced", 0)]

    out = loader.build_module_reviews(
        [_entry("CS2100")], {}, "KEY", now=1.0, force=True,
        read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
    )
    assert out[0].reviews[0].message == "forced"


def test_error_falls_back_to_stale_cache():
    def read_cache(code, ttl_seconds, now):
        return None if ttl_seconds < 10**9 else [Review("Old", "2020", "stale", 0)]

    def fetch(code, key, **kw):
        raise DisqusError(13, "rate limited")

    out = loader.build_module_reviews(
        [_entry("CS2100")], {}, "KEY", now=1.0,
        read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
    )
    assert out[0].reviews[0].message == "stale"
    assert out[0].error is not None


def test_error_no_cache_sets_error_and_continues():
    def read_cache(code, ttl_seconds, now):
        return None

    def fetch(code, key, **kw):
        raise DisqusError(13, "rate limited")

    out = loader.build_module_reviews(
        [_entry("CS2100"), _entry("CS1010")], {}, "KEY", now=1.0,
        read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
    )
    assert len(out) == 2
    assert all(m.error is not None for m in out)
    assert out[0].reviews == []
