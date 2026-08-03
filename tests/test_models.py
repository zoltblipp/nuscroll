import os

from nuscroll import models
from nuscroll.paths import nuscroll_home


def test_models_construct():
    entry = models.PlannerEntry("CS2100", "Y1S1", (0, 1, 1, "CS2100"))
    review = models.Review("Alice", "2024-01-01T00:00:00", "great mod", 3)
    mr = models.ModuleReviews("CS2100", "Computer Organisation", "Y1S1", [review])
    assert entry.module_code == "CS2100"
    assert review.likes == 3
    assert mr.reviews[0].author == "Alice"
    assert mr.error is None


def test_nuscroll_home_respects_env(tmp_path):
    os.environ["NUSCROLL_HOME"] = str(tmp_path / "home")
    try:
        home = nuscroll_home()
        assert home == tmp_path / "home"
        assert home.is_dir()
    finally:
        del os.environ["NUSCROLL_HOME"]


def test_nuscroll_home_defaults_to_dotfile(monkeypatch, tmp_path):
    monkeypatch.delenv("NUSCROLL_HOME", raising=False)
    monkeypatch.setattr("nuscroll.paths.Path.home", lambda: tmp_path)
    home = nuscroll_home()
    assert home == tmp_path / ".nuscroll"
    assert home.is_dir()
