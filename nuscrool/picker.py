"""Picker screen: choose a saved profile, or browse for a new planner file."""
from __future__ import annotations

import time
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import DirectoryTree, Footer, Header, Label, ListItem, ListView

from nuscrool import profiles as profiles_mod


class _JsonDirectoryTree(DirectoryTree):
    def filter_paths(self, paths):
        return [p for p in paths if p.is_dir() or p.suffix == ".json"]


class BrowseScreen(ModalScreen[str | None]):
    BINDINGS = [("escape", "cancel", "Cancel")]
    CSS = """
    BrowseScreen { align: center middle; }
    #browse-box {
        width: 80%; height: 80%;
        border: solid $accent; background: $surface; padding: 1 2;
    }
    """

    def __init__(self, start: Path | None = None):
        super().__init__()
        downloads = Path.home() / "Downloads"
        self.start = start or (downloads if downloads.is_dir() else Path.home())

    def compose(self) -> ComposeResult:
        with Vertical(id="browse-box"):
            yield Label("Pick a planner JSON file — Esc to cancel")
            yield _JsonDirectoryTree(str(self.start), id="tree")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.dismiss(str(event.path))

    def action_cancel(self) -> None:
        self.dismiss(None)


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
            self.app.push_screen(BrowseScreen(), self._handle_browsed)
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

    def _handle_browsed(self, path: str | None) -> None:
        if path is None:
            return
        if self._missing is not None:
            profiles_mod.add_profile(path, name=self._missing.name, now=time.time())
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
            self.app.push_screen(BrowseScreen(), self._handle_browsed)

    def action_quit(self) -> None:
        self.app.exit()
