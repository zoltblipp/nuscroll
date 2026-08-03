"""Parse a NUSMods planner export into an ordered, deduped module list."""
from __future__ import annotations

import json
from pathlib import Path

from nuscrool.models import PlannerEntry

_SEM_SUFFIX = {1: "S1", 2: "S2", 3: "ST1", 4: "ST2"}


def _start_year(year: str) -> int:
    """'2026/2027' -> 2026."""
    return int(year.split("/")[0])


def _resolve(module: dict, min_start: int) -> PlannerEntry:
    code = module.get("moduleCode")
    if not code:
        raise ValueError(f"planner module entry missing moduleCode: {module!r}")
    year = str(module.get("year", ""))
    sem = module.get("semester")

    if year == "3000":
        return PlannerEntry(code, "Exempted", (1, 0, 0, code))
    if year == "-1":
        return PlannerEntry(code, "Wishlist", (2, 0, 0, code))

    if "/" not in year:
        raise ValueError(f"unparseable year {year!r} for module {code}")
    rel = _start_year(year) - min_start + 1
    suffix = _SEM_SUFFIX.get(sem)
    if suffix is None:
        raise ValueError(f"unexpected semester {sem!r} for module {code}")
    label = f"Y{rel}{suffix}"
    return PlannerEntry(code, label, (0, rel, sem, code))


def parse_planner(data: dict) -> list[PlannerEntry]:
    min_year = data.get("minYear")
    if not min_year or "/" not in str(min_year):
        raise ValueError(f"planner missing/invalid minYear: {min_year!r}")
    min_start = _start_year(str(min_year))

    best: dict[str, PlannerEntry] = {}
    for module in data.get("modules", {}).values():
        entry = _resolve(module, min_start)
        existing = best.get(entry.module_code)
        # Lower sort_key wins; real semesters (group 0) beat specials (1, 2).
        if existing is None or entry.sort_key < existing.sort_key:
            best[entry.module_code] = entry

    return sorted(best.values(), key=lambda e: e.sort_key)


def remove_module(path: str, module_code: str) -> None:
    """Drop every entry for module_code from the planner file's modules map."""
    planner_file = Path(path)
    data = json.loads(planner_file.read_text())
    modules = data.get("modules", {})
    data["modules"] = {
        key: entry for key, entry in modules.items() if entry.get("moduleCode") != module_code
    }
    planner_file.write_text(json.dumps(data, indent=2))
