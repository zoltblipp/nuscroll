import pytest

from nuscroll import cache
from nuscroll.models import Review


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROLL_HOME", str(tmp_path))
    return tmp_path


def _reviews():
    return [Review("Bob", "2024-01-01T00:00:00", "solid mod", 2)]


def test_read_missing_returns_none(home):
    assert cache.read_cache("CS2100", ttl_seconds=86400, now=1000.0) is None


def test_write_then_read_fresh(home):
    cache.write_cache("CS2100", _reviews(), now=1000.0)
    got = cache.read_cache("CS2100", ttl_seconds=86400, now=1000.0 + 10)
    assert got is not None
    assert got[0].author == "Bob"
    assert got[0].likes == 2


def test_read_stale_returns_none(home):
    cache.write_cache("CS2100", _reviews(), now=1000.0)
    assert cache.read_cache("CS2100", ttl_seconds=100, now=1000.0 + 200) is None


def test_read_unexpected_shape_returns_none(home, tmp_path):
    import json

    path = tmp_path / "cache" / "CS2100.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetchedAt": 1000.0,
        "posts": [{"author": "Bob", "unexpectedField": "oops"}],
    }
    path.write_text(json.dumps(payload))
    assert cache.read_cache("CS2100", ttl_seconds=86400, now=1000.0 + 10) is None
