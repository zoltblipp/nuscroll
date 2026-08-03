import pytest

from nuscrool.app import NUScroolApp
from nuscrool.loading import LoadingScreen
from nuscrool.picker import PickerScreen


@pytest.fixture(autouse=True)
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("NUSCROOL_HOME", str(tmp_path))
    return tmp_path


@pytest.mark.asyncio
async def test_app_with_initial_path_pushes_loading_screen(monkeypatch):
    monkeypatch.setattr(LoadingScreen, "_load", lambda self: None)
    app = NUScroolApp(initial_path="/some/plan.json", refresh=False, api_key="KEY")
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, LoadingScreen)
        assert app.screen.path == "/some/plan.json"
        assert app.screen.force_refresh is False


@pytest.mark.asyncio
async def test_app_with_no_path_pushes_picker_screen():
    app = NUScroolApp(initial_path=None, refresh=False, api_key="KEY")
    async with app.run_test() as pilot:
        await pilot.pause()
        assert isinstance(app.screen, PickerScreen)


@pytest.mark.asyncio
async def test_app_stores_refresh_and_api_key(monkeypatch):
    monkeypatch.setattr(LoadingScreen, "_load", lambda self: None)
    app = NUScroolApp(initial_path="/x.json", refresh=True, api_key="ABC")
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.force_refresh is True
        assert app.api_key == "ABC"
