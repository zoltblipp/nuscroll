"""Composable module filters: semester, prefix, level, and single-module jump-to."""
from __future__ import annotations

import re
from dataclasses import dataclass

from nuscroll.models import ModuleReviews

_CODE_RE = re.compile(r"^([A-Z]+)(\d)")


@dataclass(frozen=True)
class FilterState:
    semesters: frozenset[str] = frozenset()
    prefixes: frozenset[str] = frozenset()
    levels: frozenset[int] = frozenset()
    module_code: str | None = None


def module_prefix(code: str) -> str | None:
    match = _CODE_RE.match(code)
    return match.group(1) if match else None


def module_level(code: str) -> int | None:
    match = _CODE_RE.match(code)
    return int(match.group(2)) if match else None


def level_label(level: int) -> str:
    return f"{level}XXX"


def semester_labels(modules: list[ModuleReviews]) -> list[str]:
    return sorted({m.label for m in modules})


def available_prefixes(modules: list[ModuleReviews]) -> list[str]:
    prefixes = {module_prefix(m.module_code) for m in modules}
    prefixes.discard(None)
    return sorted(prefixes)


def available_levels(modules: list[ModuleReviews]) -> list[int]:
    levels = {module_level(m.module_code) for m in modules}
    levels.discard(None)
    return sorted(levels)


def apply_filters(modules: list[ModuleReviews], state: FilterState) -> list[ModuleReviews]:
    if state.module_code:
        return [m for m in modules if m.module_code == state.module_code]

    shown = []
    for m in modules:
        if state.semesters and m.label not in state.semesters:
            continue
        if state.prefixes and module_prefix(m.module_code) not in state.prefixes:
            continue
        if state.levels and module_level(m.module_code) not in state.levels:
            continue
        shown.append(m)
    return shown
