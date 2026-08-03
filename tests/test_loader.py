import json

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


def test_double_fault_fallback_read_also_fails_does_not_abort():
    def read_cache(code, ttl_seconds, now):
        # Fresh cache checks (ttl_seconds=86400) return None (cache miss)
        # Fallback checks (ttl_seconds=10^9) raise OSError (disk unavailable)
        if ttl_seconds < 10**9:
            return None
        raise OSError("disk unavailable")

    def fetch(code, key, **kw):
        raise DisqusError(13, "rate limited")

    out = loader.build_module_reviews(
        [_entry("CS2100"), _entry("CS1010")], {}, "KEY", now=1.0,
        read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
    )
    assert len(out) == 2
    assert out[0].reviews == []
    assert out[0].error is not None
    assert out[1].reviews == []
    assert out[1].error is not None


def test_malformed_json_sets_error_and_continues():
    def read_cache(code, ttl_seconds, now):
        return None

    def fetch(code, key, **kw):
        raise json.JSONDecodeError("bad json", "doc", 0)

    out = loader.build_module_reviews(
        [_entry("CS2100"), _entry("CS1010")], {}, "KEY", now=1.0,
        read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
    )
    assert len(out) == 2
    assert all(m.error is not None for m in out)
    assert out[0].reviews == []


def test_concurrent_fetch_preserves_entry_order():
    import time as _time

    # First module sleeps longest so it would finish LAST if fetches ran
    # concurrently but results were appended in completion order instead
    # of entry order.
    delays = {"CS1010": 0.05, "CS2100": 0.01, "CS3230": 0.0}

    def read_cache(code, ttl_seconds, now):
        return None

    def fetch(code, key, **kw):
        _time.sleep(delays[code])
        return [Review("Net", "2024", code, 0)]

    entries = [_entry("CS1010"), _entry("CS2100"), _entry("CS3230")]
    out = loader.build_module_reviews(
        entries, {}, "KEY", now=1.0,
        read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
    )
    assert [m.module_code for m in out] == ["CS1010", "CS2100", "CS3230"]
    assert [m.reviews[0].message for m in out] == ["CS1010", "CS2100", "CS3230"]


def test_progress_called_once_per_fetched_module():
    calls = []

    def read_cache(code, ttl_seconds, now):
        return None

    def fetch(code, key, **kw):
        return [Review("Net", "2024", "x", 0)]

    entries = [_entry("CS1010"), _entry("CS2100"), _entry("CS3230")]
    loader.build_module_reviews(
        entries, {}, "KEY", now=1.0,
        read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
        progress=lambda i, total, code: calls.append((i, total, code)),
    )
    assert len(calls) == 3
    assert {c[1] for c in calls} == {3}
    assert {c[2] for c in calls} == {"CS1010", "CS2100", "CS3230"}


def test_progress_skips_cache_hits():
    calls = []

    def read_cache(code, ttl_seconds, now):
        return [Review("Cached", "2024", "hi", 0)] if code == "CS2100" else None

    def fetch(code, key, **kw):
        return [Review("Net", "2024", "x", 0)]

    entries = [_entry("CS2100"), _entry("CS1010")]
    loader.build_module_reviews(
        entries, {}, "KEY", now=1.0,
        read_cache=read_cache, fetch=fetch, write_cache=lambda *a, **k: None,
        progress=lambda i, total, code: calls.append((i, total, code)),
    )
    assert len(calls) == 1
    assert calls[0] == (0, 1, "CS1010")
