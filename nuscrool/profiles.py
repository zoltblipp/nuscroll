"""Saved planner-file profiles, so a path need not be retyped every run."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nuscrool import config


@dataclass(frozen=True)
class Profile:
    name: str
    path: str
    last_used: float = 0.0


def _to_dict(p: Profile) -> dict:
    return {"name": p.name, "path": p.path, "lastUsed": p.last_used}


def _from_dict(d: dict) -> Profile:
    return Profile(d["name"], d["path"], d.get("lastUsed", 0.0))


def list_profiles(*, get=config.get_profiles) -> list[Profile]:
    profiles = [_from_dict(d) for d in get()]
    return sorted(profiles, key=lambda p: p.last_used, reverse=True)


def _unique_name(base: str, taken: set[str]) -> str:
    if base not in taken:
        return base
    n = 2
    while f"{base} ({n})" in taken:
        n += 1
    return f"{base} ({n})"


def add_profile(
    path: str,
    name: str | None = None,
    *,
    now: float = 0.0,
    get=config.get_profiles,
    set_=config.set_profiles,
) -> Profile:
    resolved = str(Path(path).resolve())
    existing = [_from_dict(d) for d in get()]

    for i, p in enumerate(existing):
        if str(Path(p.path).resolve()) == resolved:
            updated = Profile(p.name, path, now)
            existing[i] = updated
            set_([_to_dict(p) for p in existing])
            return updated

    profile_name = name or Path(path).stem
    taken = {p.name for p in existing}
    profile_name = _unique_name(profile_name, taken)

    profile = Profile(profile_name, path, now)
    existing.append(profile)
    set_([_to_dict(p) for p in existing])
    return profile


def remove_profile(name: str, *, get=config.get_profiles, set_=config.set_profiles) -> None:
    existing = [_from_dict(d) for d in get()]
    remaining = [p for p in existing if p.name != name]
    set_([_to_dict(p) for p in remaining])


def touch_profile(
    name: str, now: float, *, get=config.get_profiles, set_=config.set_profiles
) -> None:
    existing = [_from_dict(d) for d in get()]
    updated = [
        Profile(p.name, p.path, now) if p.name == name else p for p in existing
    ]
    set_([_to_dict(p) for p in updated])


def update_path(
    name: str, path: str, now: float, *, get=config.get_profiles, set_=config.set_profiles
) -> Profile:
    """Re-point an existing profile at a new path, keeping its identity."""
    existing = [_from_dict(d) for d in get()]
    updated_profile = Profile(name, path, now)
    updated = [updated_profile if p.name == name else p for p in existing]
    set_([_to_dict(p) for p in updated])
    return updated_profile


def profile_exists_on_disk(p: Profile) -> bool:
    return Path(p.path).is_file()
