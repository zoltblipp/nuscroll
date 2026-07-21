import os

import pytest

from nuscrool import config


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROOL_HOME", str(tmp_path))
    return tmp_path


def test_get_returns_none_when_absent(home):
    assert config.get_api_key() is None


def test_set_then_get_roundtrip(home):
    config.set_api_key("ABC123")
    assert config.get_api_key() == "ABC123"


def test_set_preserves_other_keys(home):
    (home / "config.json").write_text('{"other": 1}')
    config.set_api_key("KEY")
    import json
    data = json.loads((home / "config.json").read_text())
    assert data["other"] == 1
    assert data["apiKey"] == "KEY"
