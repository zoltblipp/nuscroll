"""Loading screen: parse the planner JSON and fetch reviews off the UI thread."""
from __future__ import annotations

import json
import time
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ProgressBar

from nuscrool import metadata
from nuscrool.loader import build_module_reviews
from nuscrool.planner import parse_planner
from nuscrool.profiles import add_profile


class LoadingScreen(Screen):
    CSS = """
    LoadingScreen { align: center middle; }
    #loading-box { width: 60%; }
    #loading-status { padding: 1 0; text-align: center; }
    """

    def __init__(self, path: str, *, refresh: bool = False):
        super().__init__()
        self.path = path
        self.force_refresh = refresh

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="loading-box"):
            yield Label(f"Loading {self.path}", id="loading-status")
            yield ProgressBar(id="loading-progress", show_eta=False)
        yield Footer()

    def on_mount(self) -> None:
        self._load()

    @work(thread=True)
    def _load(self) -> None:
        planner_file = Path(self.path)
        if not planner_file.is_file():
            self._fail(f"Planner file not found: {self.path}")
            return

        try:
            data = json.loads(planner_file.read_text())
            entries = parse_planner(data)
        except (json.JSONDecodeError, ValueError) as exc:
            self._fail(f"Could not parse planner: {exc}")
            return

        if not entries:
            self._fail("No modules found in planner.")
            return

        now = time.time()
        acad_year = metadata.acad_year_from_min(data["minYear"])
        titles = metadata.fetch_titles(acad_year, now=now)

        def progress(index: int, count: int, code: str) -> None:
            self.app.call_from_thread(
                self._set_status, f"[{index + 1}/{count}] fetching {code}..."
            )

        modules = build_module_reviews(
            entries,
            titles,
            self.app.api_key,
            now=now,
            force=self.force_refresh,
            progress=progress,
        )

        add_profile(self.path, now=now)
        self.app.call_from_thread(self._show_reviews, modules)

    def _set_status(self, text: str) -> None:
        self.query_one("#loading-status", Label).update(text)

    def _show_reviews(self, modules) -> None:
        from nuscrool.reviews import ReviewsScreen

        self.app.switch_screen(ReviewsScreen(modules))

    def _fail(self, message: str) -> None:
        self.app.call_from_thread(self._show_failure, message)

    def _show_failure(self, message: str) -> None:
        from nuscrool.picker import PickerScreen

        self.app.switch_screen(PickerScreen(error=message))
