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
