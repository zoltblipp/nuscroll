"""Textual App: screen wiring."""
from __future__ import annotations

from textual.app import App

from nuscrool.loading import LoadingScreen
from nuscrool.picker import PickerScreen


class NUScroolApp(App):
    def __init__(self, *, initial_path: str | None, refresh: bool, api_key: str):
        super().__init__()
        self.initial_path = initial_path
        self.force_refresh = refresh
        self.api_key = api_key

    def on_mount(self) -> None:
        if self.initial_path:
            self.push_screen(LoadingScreen(self.initial_path, refresh=self.force_refresh))
        else:
            self.push_screen(PickerScreen())
