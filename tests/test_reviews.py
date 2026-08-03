import pytest
from textual.app import App, ComposeResult
from textual.widgets import ListView, SelectionList, Static

from nuscrool.models import ModuleReviews, Review
from nuscrool.reviews import ReviewsScreen


def _mods():
    return [
        ModuleReviews("CS2100", "Comp Org", "Y1S1", [Review("A", "2024", "hi", 0)]),
        ModuleReviews("MA1521", "Calculus", "Y1S1", []),
        ModuleReviews("CS2251", "DSA", "Y2S1", [Review("B", "2024", "yo", 1)]),
    ]


class _Harness(App):
    def __init__(self, modules):
        super().__init__()
        self.modules = modules

    def on_mount(self) -> None:
        self.push_screen(ReviewsScreen(self.modules))


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
