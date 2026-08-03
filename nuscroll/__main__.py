"""NUScroll entrypoint: parse args, ensure an API key, launch the TUI."""
from __future__ import annotations

import argparse
import sys

from nuscroll import config
from nuscroll.app import NUScrollApp

_REGISTER_URL = "https://disqus.com/api/applications/"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nuscroll", add_help=False)
    parser.add_argument("--file", dest="file")
    parser.add_argument("positional", nargs="?")
    parser.add_argument("--refresh", action="store_true")
    return parser


def resolve_planner_path(argv: list[str]) -> str | None:
    known, _ = _build_arg_parser().parse_known_args(argv)
    return known.file or known.positional


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
    refresh = _build_arg_parser().parse_known_args(argv)[0].refresh
    path = resolve_planner_path(argv)

    key = ensure_api_key()
    NUScrollApp(initial_path=path, refresh=refresh, api_key=key).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
