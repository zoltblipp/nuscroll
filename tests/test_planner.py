import pytest

from nuscroll.planner import parse_planner

SAMPLE = {
    "minYear": "2026/2027",
    "maxYear": "2029/2030",
    "modules": {
        "0": {"year": "2026/2027", "semester": 1, "moduleCode": "CS2030S"},
        "1": {"year": "3000", "semester": -2, "moduleCode": "CS1010"},
        "2": {"year": "2026/2027", "semester": 1, "moduleCode": "CS2100"},
        "4": {"year": "2026/2027", "semester": 2, "moduleCode": "MA1522"},
        "5": {"year": "-1", "semester": -1, "moduleCode": "MA1301"},
        "22": {"year": "2027/2028", "semester": 1, "moduleCode": "CS2251"},
    },
    "custom": {},
}


def test_labels_and_relative_year():
    entries = {e.module_code: e for e in parse_planner(SAMPLE)}
    assert entries["CS2030S"].label == "Y1S1"
    assert entries["MA1522"].label == "Y1S2"
    assert entries["CS2251"].label == "Y2S1"
    assert entries["CS1010"].label == "Exempted"
    assert entries["MA1301"].label == "Wishlist"


def test_sort_order_real_then_exempted_then_wishlist():
    codes = [e.module_code for e in parse_planner(SAMPLE)]
    # Y1S1 (CS2030S, CS2100 alpha), Y1S2 (MA1522), Y2S1 (CS2251), then Exempted, then Wishlist
    assert codes == ["CS2030S", "CS2100", "MA1522", "CS2251", "CS1010", "MA1301"]


def test_dedup_real_beats_special():
    data = {
        "minYear": "2026/2027",
        "modules": {
            "a": {"year": "3000", "semester": -2, "moduleCode": "CS2100"},
            "b": {"year": "2026/2027", "semester": 1, "moduleCode": "CS2100"},
        },
    }
    entries = parse_planner(data)
    assert len(entries) == 1
    assert entries[0].label == "Y1S1"


def test_missing_module_code_raises():
    data = {"minYear": "2026/2027", "modules": {"a": {"year": "2026/2027", "semester": 1}}}
    with pytest.raises(ValueError, match="moduleCode"):
        parse_planner(data)


def test_missing_min_year_raises():
    with pytest.raises(ValueError, match="minYear"):
        parse_planner({"modules": {}})
