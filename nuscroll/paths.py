"""Resolve the NUScroll home directory (config + cache root)."""
import os
from pathlib import Path


def nuscroll_home() -> Path:
    """Base dir for config and cache. Overridable via NUSCROLL_HOME."""
    override = os.environ.get("NUSCROLL_HOME")
    base = Path(override) if override else Path.home() / ".nuscroll"
    base.mkdir(parents=True, exist_ok=True)
    return base
