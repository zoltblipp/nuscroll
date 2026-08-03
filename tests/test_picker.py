import pytest
from textual.app import App
from textual.widgets import Label, ListView

from nuscrool import profiles
from nuscrool.loading import LoadingScreen
from nuscrool.picker import PickerScreen


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROOL_HOME", str(tmp_path))
    return tmp_path


class _Harness(App):
    def __init__(self, error=None):
        super().__init__()
        self._error = error

    def on_mount(self) -> None:
        self.push_screen(PickerScreen(error=self._error))


@pytest.mark.asyncio
async def test_lists_saved_profiles(home, tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    profiles.add_profile(str(plan), name="Main plan")

    app = _Harness()
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.screen.query_one("#profile-list", ListView)
        labels = [str(item.query_one(Label).content) for item in list_view.children]
        assert any("Main plan" in label for label in labels)
        assert any("Browse for file" in label for label in labels)


@pytest.mark.asyncio
async def test_missing_profile_shows_status_not_loading(home, tmp_path):
    missing = tmp_path / "gone.json"
    profiles.add_profile(str(missing), name="Gone")

    app = _Harness()
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.screen.query_one("#profile-list", ListView)
        list_view.focus()
        list_view.index = 0
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(app.screen, PickerScreen)
        status = app.screen.query_one("#status", Label)
        assert "not found" in str(status.content).lower()


@pytest.mark.asyncio
async def test_selecting_existing_profile_launches_loading(home, tmp_path, monkeypatch):
    monkeypatch.setattr(LoadingScreen, "_load", lambda self: None)
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    profiles.add_profile(str(plan), name="Main plan")

    app = _Harness()
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.screen.query_one("#profile-list", ListView)
        list_view.focus()
        list_view.index = 0
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(app.screen, LoadingScreen)
        assert app.screen.path == str(plan)


@pytest.mark.asyncio
async def test_delete_removes_profile_without_manual_navigation(home, tmp_path):
    """Regression: the first item must be highlighted by default, since it's
    appended after the ListView mounts and Textual doesn't highlight items
    added that way -- pressing 'd' straight after launch used to no-op."""
    plan = tmp_path / "plan.json"
    plan.write_text("{}")
    profiles.add_profile(str(plan), name="Main plan")

    app = _Harness()
    async with app.run_test() as pilot:
        await pilot.pause()
        list_view = app.screen.query_one("#profile-list", ListView)
        assert list_view.index == 0
        await pilot.press("d")
        await pilot.pause()

        assert profiles.list_profiles() == []
        labels = [
            str(item.query_one(Label).content) for item in list_view.children
        ]
        assert not any("Main plan" in label for label in labels)


@pytest.mark.asyncio
async def test_delete_twice_in_a_row(home, tmp_path):
    for name in ("First", "Second"):
        plan = tmp_path / f"{name}.json"
        plan.write_text("{}")
        profiles.add_profile(str(plan), name=name)

    app = _Harness()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()

        assert profiles.list_profiles() == []


@pytest.mark.asyncio
async def test_browse_opens_native_dialog_and_launches_loading(
    home, tmp_path, monkeypatch
):
    monkeypatch.setattr(LoadingScreen, "_load", lambda self: None)
    plan = tmp_path / "chosen.json"
    plan.write_text("{}")
    monkeypatch.setattr("nuscrool.picker._pick_file_native", lambda start: str(plan))

    app = _Harness()
    async with app.run_test() as pilot:
        await pilot.pause()

        list_view = app.screen.query_one("#profile-list", ListView)
        list_view.focus()
        list_view.index = [i.id for i in list_view.children].index("browse")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert isinstance(app.screen, LoadingScreen)
        assert app.screen.path == str(plan)


@pytest.mark.asyncio
async def test_browse_cancelled_stays_on_picker(home, monkeypatch):
    monkeypatch.setattr("nuscrool.picker._pick_file_native", lambda start: None)

    app = _Harness()
    async with app.run_test() as pilot:
        await pilot.pause()

        list_view = app.screen.query_one("#profile-list", ListView)
        list_view.focus()
        list_view.index = [i.id for i in list_view.children].index("browse")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await app.workers.wait_for_complete()
        await pilot.pause()

        assert isinstance(app.screen, PickerScreen)


@pytest.mark.asyncio
async def test_initial_error_shown_in_status(home):
    app = _Harness(error="Could not parse planner: boom")
    async with app.run_test() as pilot:
        await pilot.pause()
        status = app.screen.query_one("#status", Label)
        assert "boom" in str(status.content)
