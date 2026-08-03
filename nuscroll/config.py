"""Persist the Disqus public API key under ~/.nuscroll/config.json."""
from __future__ import annotations

import json

from nuscroll.paths import nuscroll_home


def _config_path():
    return nuscroll_home() / "config.json"


def _read() -> dict:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def get_api_key() -> str | None:
    return _read().get("apiKey")


def set_api_key(key: str) -> None:
    data = _read()
    data["apiKey"] = key
    _config_path().write_text(json.dumps(data, indent=2))


def get_profiles() -> list[dict]:
    return _read().get("profiles", [])


def set_profiles(profiles: list[dict]) -> None:
    data = _read()
    data["profiles"] = profiles
    _config_path().write_text(json.dumps(data, indent=2))
