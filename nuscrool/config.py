"""Persist the Disqus public API key under ~/.nuscrool/config.json."""
from __future__ import annotations

import json

from nuscrool.paths import nuscrool_home


def _config_path():
    return nuscrool_home() / "config.json"


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
