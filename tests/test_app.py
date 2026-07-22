import pytest

from nuscrool.app import NUScroolApp, filter_modules, semester_labels
from nuscrool.models import ModuleReviews, Review


def _mods():
    return [
        ModuleReviews("CS2100", "Comp Org", "Y1S1", [Review("A", "2024", "hi", 0)]),
        ModuleReviews("MA1521", "Calculus", "Y1S1", []),
        ModuleReviews("CS2251", "DSA", "Y2S1", [Review("B", "2024", "yo", 1)]),
    ]


def test_filter_none_returns_all():
    assert len(filter_modules(_mods())) == 3


def test_filter_by_module():
    out = filter_modules(_mods(), module_code="CS2100")
    assert [m.module_code for m in out] == ["CS2100"]


def test_filter_by_label():
    out = filter_modules(_mods(), label="Y1S1")
    assert [m.module_code for m in out] == ["CS2100", "MA1521"]


def test_module_filter_wins_over_label():
    out = filter_modules(_mods(), module_code="CS2251", label="Y1S1")
    assert [m.module_code for m in out] == ["CS2251"]


def test_semester_labels_unique_sorted():
    assert semester_labels(_mods()) == ["Y1S1", "Y2S1"]


@pytest.mark.asyncio
async def test_app_boots_and_shows_headers():
    app = NUScroolApp(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        stream = app.query_one("#stream")
        assert stream is not None            # stream widget mounted
    # Smoke test: app constructed, mounted, and ran without error.
    assert app.modules == _mods()


@pytest.mark.asyncio
async def test_selecting_semester_filters_stream():
    app = NUScroolApp(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        sidebar = app.query_one("#sidebar")
        stream = app.query_one("#stream")
        sidebar.focus()
        sidebar.index = [i.id for i in sidebar.children].index("sem-Y1S1")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        content = stream.content
        assert "CS2100" in content
        assert "MA1521" in content
        assert "CS2251" not in content


@pytest.mark.asyncio
async def test_selecting_module_filters_stream_to_single_module():
    app = NUScroolApp(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        sidebar = app.query_one("#sidebar")
        stream = app.query_one("#stream")
        sidebar.focus()
        sidebar.index = [i.id for i in sidebar.children].index("mod-CS2100")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        content = stream.content
        assert "CS2100" in content
        assert "MA1521" not in content
        assert "CS2251" not in content


@pytest.mark.asyncio
async def test_f_binding_focuses_sidebar():
    app = NUScroolApp(_mods())
    async with app.run_test() as pilot:
        await pilot.pause()
        sidebar = app.query_one("#sidebar")
        app.set_focus(None)
        await pilot.pause()
        assert not sidebar.has_focus

        await pilot.press("f")
        await pilot.pause()

        assert sidebar.has_focus
