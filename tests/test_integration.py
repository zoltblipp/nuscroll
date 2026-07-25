"""End-to-end pilot tests wiring NUScroolApp -> LoadingScreen -> ReviewsScreen/PickerScreen."""
import json

import pytest
from textual.widgets import Label, ListView, SelectionList, Static

from nuscrool.app import NUScroolApp
from nuscrool.loading import LoadingScreen
from nuscrool.picker import PickerScreen
from nuscrool.reviews import ReviewsScreen


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROOL_HOME", str(tmp_path))
    return tmp_path


def _write_planner(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "minYear": "2026/2027",
                "modules": {
                    "m1": {"moduleCode": "CS2100", "year": "2026/2027", "semester": 1},
                    "m2": {"moduleCode": "MA1521", "year": "2026/2027", "semester": 1},
                },
            }
        )
    )
    return plan


@pytest.mark.asyncio
async def test_explicit_path_flows_through_loading_into_reviews(
    home, tmp_path, monkeypatch
):
    plan = _write_planner(tmp_path)
    monkeypatch.setattr("nuscrool.loading.metadata.fetch_titles", lambda *a, **k: {})
    monkeypatch.setattr(
        "nuscrool.loading.build_module_reviews",
        lambda entries, titles, key, **k: [
            type("M", (), {"module_code": e.module_code, "title": "", "label": e.label,
                            "reviews": [], "error": None})()
            for e in entries
        ],
    )

    app = NUScroolApp(initial_path=str(plan), refresh=False, api_key="KEY")
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert isinstance(app.screen, ReviewsScreen)
        stream = app.screen.query_one("#stream", Static)
        assert "CS2100" in stream.content
        assert "MA1521" in stream.content


@pytest.mark.asyncio
async def test_zero_arg_picker_to_native_browse_roundtrip(home, tmp_path, monkeypatch):
    monkeypatch.setattr(LoadingScreen, "_load", lambda self: None)
    plan = _write_planner(tmp_path)
    monkeypatch.setattr("nuscrool.picker._pick_file_native", lambda start: str(plan))

    app = NUScroolApp(initial_path=None, refresh=False, api_key="KEY")
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PickerScreen)

        list_view = app.screen.query_one("#profile-list", ListView)
        labels = [str(i.query_one(Label).content) for i in list_view.children]
        assert labels == ["[ Browse for file… ]"]

        list_view.focus()
        list_view.index = 0
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert isinstance(app.screen, LoadingScreen)
        assert app.screen.path == str(plan)


@pytest.mark.asyncio
async def test_missing_initial_path_falls_back_to_picker_with_error(home):
    app = NUScroolApp(initial_path="/nowhere/plan.json", refresh=False, api_key="KEY")
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert isinstance(app.screen, PickerScreen)
        status = app.screen.query_one("#status", Label)
        assert "not found" in str(status.content).lower()
