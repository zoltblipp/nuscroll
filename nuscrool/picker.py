"""Picker screen: choose a saved profile, or browse for a new planner file."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView

from nuscrool import profiles as profiles_mod

# Runs Tk in its own process so its Cocoa/Tcl run loop never shares a thread
# with Textual's asyncio loop (in-process tkinter deadlocked on macOS). Also
# activates itself via osascript so the dialog opens frontmost, since a
# background subprocess doesn't get window focus by default on macOS.
_HELPER_SRC = """
import os, sys, subprocess
if sys.platform == "darwin":
    subprocess.run([
        "osascript", "-e",
        'tell application "System Events" to set frontmost of every process '
        f'whose unix id is {os.getpid()} to true',
    ])
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()
root.attributes("-topmost", True)
path = filedialog.askopenfilename(
    initialdir=sys.argv[1],
    title="Pick a planner JSON file",
    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
)
root.destroy()
print(path)
"""


def _pick_file_native(start: Path) -> str | None:
    """Block on a native OS file-open dialog and return the chosen path, or None."""
    result = subprocess.run(
        [sys.executable, "-c", _HELPER_SRC, str(start)],
        capture_output=True,
        text=True,
    )
    path = result.stdout.strip()
    return path or None


class PickerScreen(Screen):
    CSS = """
    #status { padding: 0 1; color: $text-muted; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "delete_selected", "Delete"),
        ("r", "repoint_missing", "Re-point"),
    ]

    def __init__(self, error: str | None = None):
        super().__init__()
        self._profiles: list[profiles_mod.Profile] = []
        self._missing: profiles_mod.Profile | None = None
        self._error = error

    def compose(self) -> ComposeResult:
        yield Header()
        yield ListView(id="profile-list")
        yield Label("", id="status")
        yield Footer()

    async def on_mount(self) -> None:
        await self._reload()
        if self._error:
            self.query_one("#status", Label).update(f"[red]{self._error}[/red]")
            self._error = None

    async def _reload(self) -> None:
        self._profiles = profiles_mod.list_profiles()
        self._missing = None
        list_view = self.query_one("#profile-list", ListView)
        await list_view.clear()
        for i, p in enumerate(self._profiles):
            exists = profiles_mod.profile_exists_on_disk(p)
            tag = "" if exists else "  [red](missing)[/red]"
            list_view.append(
                ListItem(Label(f"{p.name}  [dim]{p.path}[/dim]{tag}"), id=f"profile-{i}")
            )
        list_view.append(ListItem(Label("[ Browse for file… ]"), id="browse"))
        self.query_one("#status", Label).update("")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == "browse":
            self._browse_native()
            return

        index = int(item_id.removeprefix("profile-"))
        profile = self._profiles[index]
        if profiles_mod.profile_exists_on_disk(profile):
            profiles_mod.touch_profile(profile.name, time.time())
            self._launch(profile.path)
        else:
            self._missing = profile
            self.query_one("#status", Label).update(
                f"[red]'{profile.name}' file not found.[/red] "
                "Press r to browse a new location, d to delete."
            )

    def _browse_native(self) -> None:
        downloads = Path.home() / "Downloads"
        start = downloads if downloads.is_dir() else Path.home()
        self._run_picker(start)

    @work(thread=True)
    def _run_picker(self, start: Path) -> None:
        path = _pick_file_native(start)
        self.app.call_from_thread(self._handle_browsed, path)

    def _handle_browsed(self, path: str | None) -> None:
        if path is None:
            return
        if self._missing is not None:
            profiles_mod.update_path(self._missing.name, path, time.time())
        self._launch(path)

    def _launch(self, path: str) -> None:
        from nuscrool.loading import LoadingScreen

        self.app.push_screen(LoadingScreen(path))

    async def action_delete_selected(self) -> None:
        list_view = self.query_one("#profile-list", ListView)
        if list_view.index is None:
            return
        item_id = list_view.children[list_view.index].id or ""
        if not item_id.startswith("profile-"):
            return
        index = int(item_id.removeprefix("profile-"))
        profiles_mod.remove_profile(self._profiles[index].name)
        await self._reload()

    def action_repoint_missing(self) -> None:
        if self._missing is not None:
            self._browse_native()

    def action_quit(self) -> None:
        self.app.exit()
