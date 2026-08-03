import json

import pytest

from nuscroll import __main__ as cli


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROLL_HOME", str(tmp_path))
    (tmp_path / "config.json").write_text(json.dumps({"apiKey": "TESTKEY"}))
    return tmp_path


class _FakeApp:
    last_kwargs: dict | None = None

    def __init__(self, **kwargs):
        _FakeApp.last_kwargs = kwargs

    def run(self):
        pass


@pytest.fixture(autouse=True)
def fake_app(monkeypatch):
    _FakeApp.last_kwargs = None
    monkeypatch.setattr(cli, "NUScrollApp", _FakeApp)
    return _FakeApp


def test_resolve_path_from_flag():
    assert cli.resolve_planner_path(["--file", "/x/plan.json"]) == "/x/plan.json"


def test_resolve_path_from_positional():
    assert cli.resolve_planner_path(["/y/plan.json"]) == "/y/plan.json"


def test_resolve_path_none_when_absent():
    assert cli.resolve_planner_path([]) is None


def test_ensure_api_key_returns_existing():
    key = cli.ensure_api_key(get=lambda: "EXISTING", set_=lambda k: None)
    assert key == "EXISTING"


def test_ensure_api_key_prompts_and_persists():
    saved = {}
    key = cli.ensure_api_key(
        input_fn=lambda _: "NEWKEY",
        get=lambda: None,
        set_=lambda k: saved.setdefault("k", k),
    )
    assert key == "NEWKEY"
    assert saved["k"] == "NEWKEY"


def test_main_builds_app_with_explicit_path(home):
    rc = cli.main(["--file", "/some/plan.json"])
    assert rc == 0
    assert _FakeApp.last_kwargs == {
        "initial_path": "/some/plan.json",
        "refresh": False,
        "api_key": "TESTKEY",
    }


def test_main_builds_app_with_no_path(home):
    rc = cli.main([])
    assert rc == 0
    assert _FakeApp.last_kwargs["initial_path"] is None


def test_main_passes_refresh_flag(home):
    cli.main(["--file", "/some/plan.json", "--refresh"])
    assert _FakeApp.last_kwargs["refresh"] is True
