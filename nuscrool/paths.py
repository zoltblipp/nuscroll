"""Resolve the NUScrool home directory (config + cache root)."""
import os
from pathlib import Path


def nuscrool_home() -> Path:
    """Base dir for config and cache. Overridable via NUSCROOL_HOME."""
    override = os.environ.get("NUSCROOL_HOME")
    base = Path(override) if override else Path.home() / ".nuscrool"
    base.mkdir(parents=True, exist_ok=True)
    return base
