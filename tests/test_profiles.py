import json

import pytest

from nuscroll import profiles


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROLL_HOME", str(tmp_path))
    return tmp_path


def test_list_profiles_empty_when_absent(home):
    assert profiles.list_profiles() == []


def test_add_then_list_roundtrip(home, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    profiles.add_profile(str(plan), now=100.0)

    out = profiles.list_profiles()
    assert len(out) == 1
    assert out[0].name == "plan"
    assert out[0].path == str(plan)
    assert out[0].last_used == 100.0


def test_add_profile_derives_name_from_stem(home, tmp_path):
    plan = tmp_path / "my-planner.json"
    plan.write_text("{}")
    p = profiles.add_profile(str(plan))
    assert p.name == "my-planner"


def test_add_profile_explicit_name(home, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    p = profiles.add_profile(str(plan), name="Main plan")
    assert p.name == "Main plan"


def test_add_profile_name_collision_gets_suffix(home, tmp_path):
    plan_a = tmp_path / "a" / "plan.json"
    plan_a.parent.mkdir()
    plan_a.write_text("{}")
    plan_b = tmp_path / "b" / "plan.json"
    plan_b.parent.mkdir()
    plan_b.write_text("{}")

    profiles.add_profile(str(plan_a))
    p2 = profiles.add_profile(str(plan_b))

    names = {p.name for p in profiles.list_profiles()}
    assert names == {"plan", "plan (2)"}
    assert p2.name == "plan (2)"


def test_add_profile_dedupes_on_resolved_path(home, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}")

    profiles.add_profile(str(plan), now=1.0)
    profiles.add_profile(str(plan), now=2.0)

    out = profiles.list_profiles()
    assert len(out) == 1
    assert out[0].last_used == 2.0


def test_remove_profile(home, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    profiles.add_profile(str(plan))

    profiles.remove_profile("plan")

    assert profiles.list_profiles() == []


def test_touch_profile_updates_last_used(home, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    profiles.add_profile(str(plan), now=1.0)

    profiles.touch_profile("plan", 50.0)

    assert profiles.list_profiles()[0].last_used == 50.0

def test_list_profiles_sorted_by_last_used_desc(home, tmp_path):
    a = tmp_path / "a.json"
    a.write_text("{}")
    b = tmp_path / "b.json"
    b.write_text("{}")
    profiles.add_profile(str(a), now=1.0)
    profiles.add_profile(str(b), now=2.0)

    out = profiles.list_profiles()
    assert [p.name for p in out] == ["b", "a"]


def test_missing_profiles_key_returns_empty(home):
    (home / "config.json").write_text('{"apiKey": "x"}')
    assert profiles.list_profiles() == []


def test_corrupt_config_returns_empty(home):
    (home / "config.json").write_text("{not valid json")
    assert profiles.list_profiles() == []


def test_profile_exists_on_disk(home, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    p = profiles.add_profile(str(plan))
    assert profiles.profile_exists_on_disk(p)

    plan.unlink()
    assert not profiles.profile_exists_on_disk(p)


def test_add_profile_preserves_api_key(home, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    (home / "config.json").write_text(json.dumps({"apiKey": "SECRET"}))

    profiles.add_profile(str(plan))

    data = json.loads((home / "config.json").read_text())
    assert data["apiKey"] == "SECRET"
    assert len(data["profiles"]) == 1
