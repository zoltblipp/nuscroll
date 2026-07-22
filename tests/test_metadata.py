import pytest

from nuscrool import metadata


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROOL_HOME", str(tmp_path))
    return tmp_path


def test_acad_year_format():
    assert metadata.acad_year_from_min("2026/2027") == "2026-2027"


def test_fetch_titles_maps_and_caches(home):
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return [
            {"moduleCode": "CS2100", "title": "Computer Organisation", "semesters": [1]},
            {"moduleCode": "MA1521", "title": "Calculus for Computing", "semesters": [1, 2]},
        ]

    titles = metadata.fetch_titles("2026-2027", now=1000.0, fetch_json=fake_fetch)
    assert titles["CS2100"] == "Computer Organisation"

    # Second call within TTL hits cache, not network.
    titles2 = metadata.fetch_titles("2026-2027", now=1000.0 + 10, fetch_json=fake_fetch)
    assert titles2["MA1521"] == "Calculus for Computing"
    assert len(calls) == 1


def test_fetch_titles_network_error_returns_empty(home):
    def boom(url):
        raise OSError("no network")

    assert metadata.fetch_titles("2026-2027", now=1.0, fetch_json=boom) == {}
