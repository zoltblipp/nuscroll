"""Textual TUI: filter sidebar + review stream sorted by module."""
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from nuscrool.models import ModuleReviews


def filter_modules(
    modules: list[ModuleReviews],
    *,
    module_code: str | None = None,
    label: str | None = None,
) -> list[ModuleReviews]:
    if module_code:
        return [m for m in modules if m.module_code == module_code]
    if label:
        return [m for m in modules if m.label == label]
    return list(modules)


def semester_labels(modules: list[ModuleReviews]) -> list[str]:
    return sorted({m.label for m in modules})


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


class NUScroolApp(App):
    CSS = """
    #sidebar { width: 24; border-right: solid $accent; }
    #stream { padding: 1 2; }
    """
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("f", "focus_filters", "Filters"),
    ]

    def __init__(self, modules: list[ModuleReviews]):
        super().__init__()
        self.modules = modules

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            items = [ListItem(Label("All"), id="all")]
            for lbl in semester_labels(self.modules):
                items.append(ListItem(Label(lbl), id=f"sem-{lbl}"))
            for m in self.modules:
                items.append(ListItem(Label(m.module_code), id=f"mod-{m.module_code}"))
            yield ListView(*items, id="sidebar")
            with VerticalScroll():
                yield Static(self._stream_text(self.modules), id="stream", markup=True)
        yield Footer()

    def _stream_text(self, mods: list[ModuleReviews]) -> str:
        if not mods:
            return "[dim]No modules match this filter.[/dim]"
        separator = "\n" + "─" * 60 + "\n\n"
        return separator.join(_render_module(m) for m in mods)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or "all"
        if item_id == "all":
            shown = filter_modules(self.modules)
        elif item_id.startswith("sem-"):
            shown = filter_modules(self.modules, label=item_id[4:])
        elif item_id.startswith("mod-"):
            shown = filter_modules(self.modules, module_code=item_id[4:])
        else:
            shown = self.modules
        self.query_one("#stream", Static).update(self._stream_text(shown))

    def action_focus_filters(self) -> None:
        self.query_one("#sidebar", ListView).focus()
