import json

import pytest

from nuscrool import __main__ as cli


def test_resolve_path_from_flag():
    assert cli.resolve_planner_path(["--file", "/x/plan.json"]) == "/x/plan.json"


def test_resolve_path_from_positional():
    assert cli.resolve_planner_path(["/y/plan.json"]) == "/y/plan.json"


def test_resolve_path_prompts_when_absent():
    got = cli.resolve_planner_path([], input_fn=lambda _: "/z/plan.json")
    assert got == "/z/plan.json"


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


def test_main_bad_path_returns_error(tmp_path, capsys):
    rc = cli.main(["--file", str(tmp_path / "missing.json")])
    assert rc == 1
    assert "not found" in capsys.readouterr().out.lower()


def test_main_malformed_json_returns_error(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json")
    rc = cli.main(["--file", str(path)])
    assert rc == 1
    assert "parse" in capsys.readouterr().out.lower()


def test_main_no_modules_returns_error(tmp_path, capsys):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"minYear": "2026/2027", "modules": {}}))
    rc = cli.main(["--file", str(path)])
    assert rc == 1
    assert "no modules" in capsys.readouterr().out.lower()
