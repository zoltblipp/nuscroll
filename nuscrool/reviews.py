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
    #sidebar SelectionList { height: auto; max-height: 8; }
    #sidebar Label { padding: 1 1 0 1; text-style: bold; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f", "focus_filters", "Filters"),
        ("c", "clear_filters", "Clear filters"),
    ]

    def __init__(self, modules: list[ModuleReviews]):
        super().__init__()
        self.modules = modules
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
            with VerticalScroll():
                yield Static(self._stream_text(self.modules), id="stream", markup=True)
        yield Footer()

    def _stream_text(self, mods: list[ModuleReviews]) -> str:
        if not mods:
            return "[dim]No modules match this filter.[/dim]"
        status = f"[dim]showing {len(mods)} of {len(self.modules)} modules[/dim]\n\n"
        separator = "\n" + "─" * 60 + "\n\n"
        return status + separator.join(_render_module(m) for m in mods)

    def _refresh_stream(self) -> None:
        shown = apply_filters(self.modules, self.filter_state)
        self.query_one("#stream", Static).update(self._stream_text(shown))

    def on_selection_list_selected_changed(
        self, event: SelectionList.SelectedChanged
    ) -> None:
        self.filter_state = FilterState(
            semesters=frozenset(self.query_one("#f-sem", SelectionList).selected),
            prefixes=frozenset(self.query_one("#f-prefix", SelectionList).selected),
            levels=frozenset(self.query_one("#f-level", SelectionList).selected),
        )
        self._refresh_stream()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or "all"
        if item_id.startswith("mod-"):
            self.filter_state = FilterState(module_code=item_id[4:])
        else:
            state = self.filter_state
            self.filter_state = FilterState(
                semesters=state.semesters, prefixes=state.prefixes, levels=state.levels
            )
        self._refresh_stream()

    def action_focus_filters(self) -> None:
        self.query_one("#f-sem", SelectionList).focus()

    def action_clear_filters(self) -> None:
        self.query_one("#f-sem", SelectionList).deselect_all()
        self.query_one("#f-prefix", SelectionList).deselect_all()
        self.query_one("#f-level", SelectionList).deselect_all()
        self.query_one("#module-list", ListView).index = None
        self.filter_state = FilterState()
        self._refresh_stream()
