"""Reviews screen: faceted filter sidebar + review stream sorted by module."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, SelectionList, Static

from nuscrool.filters import (
    FilterState,
    apply_filters,
    available_levels,
    available_prefixes,
    level_label,
    semester_labels,
)
from nuscrool.models import ModuleReviews
from nuscrool.planner import remove_module


def _render_module(m: ModuleReviews) -> str:
    title = f" — {m.title}" if m.title else ""
    header = f"[b]{m.module_code}{title}[/b]  [dim]{m.label}[/dim]  ({len(m.reviews)} reviews)"
    lines = [header]
    if m.error:
        lines.append(f"[red]fetch failed: {m.error}[/red]")
    if not m.reviews:
        lines.append("[dim]No reviews yet[/dim]")
    for r in m.reviews:
        lines.append(f"[cyan]{r.author}[/cyan]  [dim]{r.created_at}  ♥ {r.likes}[/dim]")
        lines.append(r.message)
        lines.append("")
    return "\n".join(lines)


class ReviewsScreen(Screen):
    CSS = """
    #sidebar { width: 28; border-right: solid $accent; }
    #stream { padding: 1 2; }
    #stream-status { color: $text-muted; padding-bottom: 1; }
    .module-block { margin-bottom: 1; border-bottom: solid $accent 30%; padding-bottom: 1; }
    #sidebar SelectionList { height: auto; max-height: 8; }
    #sidebar Label { padding: 1 1 0 1; text-style: bold; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f", "focus_filters", "Filters"),
        ("c", "clear_filters", "Clear filters"),
        ("d", "delete_module", "Delete mod"),
    ]

    def __init__(self, modules: list[ModuleReviews], path: str):
        super().__init__()
        self.modules = modules
        self.path = path
        self.filter_state = FilterState()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with VerticalScroll(id="sidebar"):
                yield Label("Semester")
                yield SelectionList(
                    *[(lbl, lbl) for lbl in semester_labels(self.modules)],
                    id="f-sem",
                )
                yield Label("Prefix")
                yield SelectionList(
                    *[(p, p) for p in available_prefixes(self.modules)],
                    id="f-prefix",
                )
                yield Label("Level")
                yield SelectionList(
                    *[(level_label(d), d) for d in available_levels(self.modules)],
                    id="f-level",
                )
                yield Label("Modules")
                items = [ListItem(Label("All"), id="all")]
                for m in self.modules:
                    items.append(ListItem(Label(m.module_code), id=f"mod-{m.module_code}"))
                yield ListView(*items, id="module-list")
            with VerticalScroll(id="stream"):
                yield Label("", id="stream-status")
        yield Footer()

    async def on_mount(self) -> None:
        await self._refresh_stream()

    async def _refresh_stream(self) -> None:
        # One Static per module, not one giant markup string for the whole
        # stream: a single Static covering hundreds of reviews makes Rich's
        # markup parsing/layout effectively hang (verified: a 450KB blob
        # never finished mounting; split per-module it mounts in ~1s).
        shown = apply_filters(self.modules, self.filter_state)
        status = self.query_one("#stream-status", Label)
        stream = self.query_one("#stream", VerticalScroll)
        await stream.remove_children(".module-block")

        if not shown:
            status.update("[dim]No modules match this filter.[/dim]")
            return

        status.update(f"[dim]showing {len(shown)} of {len(self.modules)} modules[/dim]")
        await stream.mount_all(
            Static(_render_module(m), markup=True, classes="module-block")
            for m in shown
        )

    async def on_selection_list_selected_changed(
        self, event: SelectionList.SelectedChanged
    ) -> None:
        self.filter_state = FilterState(
            semesters=frozenset(self.query_one("#f-sem", SelectionList).selected),
            prefixes=frozenset(self.query_one("#f-prefix", SelectionList).selected),
            levels=frozenset(self.query_one("#f-level", SelectionList).selected),
        )
        await self._refresh_stream()

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or "all"
        if item_id.startswith("mod-"):
            self.filter_state = FilterState(module_code=item_id[4:])
        else:
            state = self.filter_state
            self.filter_state = FilterState(
                semesters=state.semesters, prefixes=state.prefixes, levels=state.levels
            )
        await self._refresh_stream()

    def action_quit(self) -> None:
        self.app.exit()

    async def action_delete_module(self) -> None:
        module_list = self.query_one("#module-list", ListView)
        if module_list.index is None:
            return
        item_id = module_list.children[module_list.index].id or ""
        if not item_id.startswith("mod-"):
            return
        code = item_id.removeprefix("mod-")

        self.modules = [m for m in self.modules if m.module_code != code]
        remove_module(self.path, code)
        await module_list.pop(module_list.index)

        if self.filter_state.module_code == code:
            self.filter_state = FilterState()
        await self._refresh_stream()

    def action_focus_filters(self) -> None:
        self.query_one("#f-sem", SelectionList).focus()

    async def action_clear_filters(self) -> None:
        self.query_one("#f-sem", SelectionList).deselect_all()
        self.query_one("#f-prefix", SelectionList).deselect_all()
        self.query_one("#f-level", SelectionList).deselect_all()
        self.query_one("#module-list", ListView).index = None
        self.filter_state = FilterState()
        await self._refresh_stream()
