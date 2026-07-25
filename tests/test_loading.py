import json

import pytest
from textual.app import App

from nuscrool.loading import LoadingScreen
from nuscrool.picker import PickerScreen
from nuscrool.reviews import ReviewsScreen


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROOL_HOME", str(tmp_path))
    return tmp_path


class _Harness(App):
    def __init__(self, path, *, refresh=False, api_key="KEY"):
        super().__init__()
        self.api_key = api_key
        self._path = path
        self._refresh = refresh

    def on_mount(self) -> None:
        self.push_screen(LoadingScreen(self._path, refresh=self._refresh))


@pytest.mark.asyncio
async def test_missing_file_switches_to_picker_with_error(home):
    app = _Harness("/does/not/exist.json")
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, PickerScreen)


@pytest.mark.asyncio
async def test_malformed_json_switches_to_picker_with_error(home, tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json")
    app = _Harness(str(path))
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, PickerScreen)


@pytest.mark.asyncio
async def test_empty_planner_switches_to_picker_with_error(home, tmp_path):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"minYear": "2026/2027", "modules": {}}))
    app = _Harness(str(path))
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, PickerScreen)


@pytest.mark.asyncio
async def test_valid_planner_switches_to_reviews_and_saves_profile(
    home, tmp_path, monkeypatch
):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "minYear": "2026/2027",
                "modules": {
                    "m1": {"moduleCode": "CS2100", "year": "2026/2027", "semester": 1}
                },
            }
        )
    )

    monkeypatch.setattr(
        "nuscrool.loading.metadata.fetch_titles", lambda *a, **k: {}
    )
    monkeypatch.setattr(
        "nuscrool.loading.build_module_reviews",
        lambda *a, **k: [],
    )

    app = _Harness(str(plan))
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, ReviewsScreen)

    from nuscrool import profiles

    saved = profiles.list_profiles()
    assert len(saved) == 1
    assert saved[0].path == str(plan)
