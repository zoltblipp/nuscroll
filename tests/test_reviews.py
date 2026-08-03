import json
import tempfile

import pytest
from textual.app import App, ComposeResult
from textual.widgets import ListView, SelectionList, Static

from nuscroll.models import ModuleReviews, Review
from nuscroll.reviews import _PREVIEW_LIMIT, _render_module, ReviewsScreen


def _mods():
    return [
        ModuleReviews("CS2100", "Comp Org", "Y1S1", [Review("A", "2024", "hi", 0)]),
        ModuleReviews("MA1521", "Calculus", "Y1S1", []),
        ModuleReviews("CS2251", "DSA", "Y2S1", [Review("B", "2024", "yo", 1)]),
    ]


def _planner_path(modules) -> str:
    """Write a planner JSON whose moduleCodes match the given ModuleReviews list."""
    data = {
        "minYear": "2026/2027",
        "modules": {
            f"m{i}": {"moduleCode": m.module_code, "year": "2026/2027", "semester": 1}
            for i, m in enumerate(modules)
        },
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    with open(fd, "w") as f:
        json.dump(data, f)
    return path


class _Harness(App):
    def __init__(self, modules, path=None):
        super().__init__()
        self.modules = modules
        self.path = path or _planner_path(modules)

    def on_mount(self) -> None:
        self.push_screen(ReviewsScreen(self.modules, self.path))


def _stream_content(app) -> str:
    """Join text from every per-module Static block (see ReviewsScreen._refresh_stream)."""
    blocks = app.screen.query(".module-block")
    return "\n".join(str(b.content) for b in blocks)


@pytest.mark.asyncio
async def test_app_boots_and_shows_headers():
    app = _Harness(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        stream = app.screen.query_one("#stream")
        assert stream is not None
    assert app.modules == _mods()


@pytest.mark.asyncio
async def test_selecting_semester_filters_stream():
    app = _Harness(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        sem_list = app.screen.query_one("#f-sem", SelectionList)
        sem_list.focus()
        sem_list.highlighted = [o.value for o in sem_list._options].index("Y1S1")
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()

        content = _stream_content(app)
        assert "CS2100" in content
        assert "MA1521" in content
        assert "CS2251" not in content


@pytest.mark.asyncio
async def test_selecting_two_semesters_ors_within_facet():
    app = _Harness(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        sem_list = app.screen.query_one("#f-sem", SelectionList)
        sem_list.focus()
        for label in ("Y1S1", "Y2S1"):
            sem_list.highlighted = [o.value for o in sem_list._options].index(label)
            await pilot.pause()
            await pilot.press("space")
            await pilot.pause()

        content = _stream_content(app)
        assert "CS2100" in content
        assert "MA1521" in content
        assert "CS2251" in content


@pytest.mark.asyncio
async def test_and_across_facets_prefix_and_semester():
    app = _Harness(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        sem_list = app.screen.query_one("#f-sem", SelectionList)
        prefix_list = app.screen.query_one("#f-prefix", SelectionList)

        sem_list.focus()
        sem_list.highlighted = [o.value for o in sem_list._options].index("Y1S1")
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()

        prefix_list.focus()
        prefix_list.highlighted = [o.value for o in prefix_list._options].index("CS")
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()

        content = _stream_content(app)
        assert "CS2100" in content
        assert "MA1521" not in content
        assert "CS2251" not in content


@pytest.mark.asyncio
async def test_selecting_module_filters_stream_to_single_module():
    app = _Harness(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        module_list = app.screen.query_one("#module-list", ListView)
        module_list.focus()
        module_list.index = [i.id for i in module_list.children].index("mod-CS2100")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        content = _stream_content(app)
        assert "CS2100" in content
        assert "MA1521" not in content
        assert "CS2251" not in content


@pytest.mark.asyncio
async def test_clear_filters_resets_to_all():
    app = _Harness(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        sem_list = app.screen.query_one("#f-sem", SelectionList)
        sem_list.focus()
        sem_list.highlighted = [o.value for o in sem_list._options].index("Y1S1")
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert "CS2251" not in _stream_content(app)

        await pilot.press("c")
        await pilot.pause()

        content = _stream_content(app)
        assert "CS2251" in content
        assert "CS2100" in content


@pytest.mark.asyncio
async def test_f_binding_focuses_semester_filter():
    app = _Harness(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        sem_list = app.screen.query_one("#f-sem", SelectionList)
        app.set_focus(None)
        await pilot.pause()
        assert not sem_list.has_focus

        await pilot.press("f")
        await pilot.pause()

        assert sem_list.has_focus


@pytest.mark.asyncio
async def test_q_binding_quits_app():
    app = _Harness(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()

        assert app.return_code == 0


@pytest.mark.asyncio
async def test_delete_module_removes_from_list_stream_and_json():
    mods = _mods()
    path = _planner_path(mods)
    app = _Harness(mods, path=path)
    async with app.run_test() as pilot:
        await pilot.pause()
        module_list = app.screen.query_one("#module-list", ListView)
        module_list.focus()
        module_list.index = [i.id for i in module_list.children].index("mod-CS2100")
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()

        content = _stream_content(app)
        assert "CS2100" not in content
        assert "MA1521" in content
        assert "CS2251" in content

        ids = [i.id for i in module_list.children]
        assert "mod-CS2100" not in ids

        saved = json.loads(open(path).read())
        codes = {m["moduleCode"] for m in saved["modules"].values()}
        assert codes == {"MA1521", "CS2251"}


@pytest.mark.asyncio
async def test_delete_module_noop_when_all_is_highlighted():
    mods = _mods()
    path = _planner_path(mods)
    app = _Harness(mods, path=path)
    async with app.run_test() as pilot:
        await pilot.pause()
        module_list = app.screen.query_one("#module-list", ListView)
        assert module_list.index == 0  # "All" item

        await pilot.press("d")
        await pilot.pause()

        content = _stream_content(app)
        assert "CS2100" in content
        saved = json.loads(open(path).read())
        codes = {m["moduleCode"] for m in saved["modules"].values()}
        assert codes == {"CS2100", "MA1521", "CS2251"}


@pytest.mark.asyncio
async def test_delete_module_while_jumped_to_it_falls_back_to_all():
    mods = _mods()
    path = _planner_path(mods)
    app = _Harness(mods, path=path)
    async with app.run_test() as pilot:
        await pilot.pause()
        module_list = app.screen.query_one("#module-list", ListView)
        module_list.focus()
        module_list.index = [i.id for i in module_list.children].index("mod-CS2100")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert _stream_content(app).count("Comp Org") == 1

        await pilot.press("d")
        await pilot.pause()

        content = _stream_content(app)
        assert "CS2100" not in content
        assert "MA1521" in content
        assert "CS2251" in content


def test_render_module_caps_reviews_by_default():
    reviews = [Review(f"A{i}", "2024", f"msg{i}", 0) for i in range(_PREVIEW_LIMIT + 3)]
    m = ModuleReviews("CS2100", "Comp Org", "Y1S1", reviews)

    out = _render_module(m)

    assert "msg0" in out
    assert f"msg{_PREVIEW_LIMIT - 1}" in out
    assert f"msg{_PREVIEW_LIMIT}" not in out
    assert "+3 more" in out


def test_render_module_full_shows_every_review():
    reviews = [Review(f"A{i}", "2024", f"msg{i}", 0) for i in range(_PREVIEW_LIMIT + 3)]
    m = ModuleReviews("CS2100", "Comp Org", "Y1S1", reviews)

    out = _render_module(m, full=True)

    for i in range(len(reviews)):
        assert f"msg{i}" in out
    assert "more" not in out


def test_render_module_escapes_brackets_in_review_text():
    # rich.markup.escape() only escapes brackets that actually look like
    # tag syntax (matching Rich's own parser grammar) -- "[10/10]" is safe
    # as-is since Rich wouldn't parse it as a tag either way, but something
    # shaped like "[bold]"/"[/bold]" must be neutralized or it renders styled.
    m = ModuleReviews(
        "CS2100", "Comp Org", "Y1S1",
        [Review("[bold red]hacker[/bold red]", "2024", "nice mod [bold]great[/bold]", 0)],
    )

    out = _render_module(m)

    assert "[bold red]hacker[/bold red]" not in out
    assert "\\[bold red]hacker\\[/bold red]" in out
    assert "nice mod \\[bold]great\\[/bold]" in out


@pytest.mark.asyncio
async def test_all_view_caps_reviews_but_jump_to_shows_full():
    reviews = [Review(f"A{i}", "2024", f"msg{i}", 0) for i in range(_PREVIEW_LIMIT + 3)]
    mods = [ModuleReviews("CS2100", "Comp Org", "Y1S1", reviews)]
    app = _Harness(mods)
    async with app.run_test() as pilot:
        await pilot.pause()
        assert f"msg{_PREVIEW_LIMIT}" not in _stream_content(app)

        module_list = app.screen.query_one("#module-list", ListView)
        module_list.focus()
        module_list.index = [i.id for i in module_list.children].index("mod-CS2100")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert f"msg{_PREVIEW_LIMIT}" in _stream_content(app)
