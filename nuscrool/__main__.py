"""NUScrool entrypoint: wire planner, reviews, and the TUI together."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from nuscrool import config, metadata
from nuscrool.app import NUScroolApp
from nuscrool.loader import build_module_reviews
from nuscrool.planner import parse_planner

_REGISTER_URL = "https://disqus.com/api/applications/"


def resolve_planner_path(argv: list[str], input_fn=input) -> str:
    parser = argparse.ArgumentParser(prog="nuscrool", add_help=False)
    parser.add_argument("--file", dest="file")
    parser.add_argument("positional", nargs="?")
    parser.add_argument("--refresh", action="store_true")
    known, _ = parser.parse_known_args(argv)
    path = known.file or known.positional
    if not path:
        path = input_fn("Path to NUSMods planner JSON: ").strip()
    return path


def ensure_api_key(input_fn=input, get=config.get_api_key, set_=config.set_api_key) -> str:
    key = get()
    if key:
        return key
    print(f"A free Disqus public API key is required. Register one at:\n  {_REGISTER_URL}")
    key = input_fn("Paste your Disqus public API key: ").strip()
    set_(key)
    return key


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    refresh = "--refresh" in argv

    path = resolve_planner_path(argv)
    planner_file = Path(path)
    if not planner_file.is_file():
        print(f"Planner file not found: {path}")
        return 1

    try:
        data = json.loads(planner_file.read_text())
        entries = parse_planner(data)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"Could not parse planner: {exc}")
        return 1

    if not entries:
        print("No modules found in planner.")
        return 1

    key = ensure_api_key()
    now = time.time()
    acad_year = metadata.acad_year_from_min(data["minYear"])
    titles = metadata.fetch_titles(acad_year, now=now)

    def progress(i, total, code):
        print(f"[{i + 1}/{total}] fetching {code}...", flush=True)

    modules = build_module_reviews(
        entries, titles, key, now=now, force=refresh, progress=progress
    )
    NUScroolApp(modules).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
