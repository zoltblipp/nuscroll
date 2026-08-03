from nuscroll.filters import (
    FilterState,
    apply_filters,
    available_levels,
    available_prefixes,
    level_label,
    module_level,
    module_prefix,
    semester_labels,
)
from nuscroll.models import ModuleReviews


def _mods():
    return [
        ModuleReviews("CS2100", "Comp Org", "Y1S1", []),
        ModuleReviews("CS2040C", "DSA", "Y1S2", []),
        ModuleReviews("MA1521", "Calculus", "Y1S1", []),
        ModuleReviews("GEA1000", "Data Literacy", "Y2S1", []),
        ModuleReviews("CS3230", "Algo", "Y2S1", []),
    ]


def test_module_prefix_basic():
    assert module_prefix("CS2100") == "CS"


def test_module_prefix_letter_suffix():
    assert module_prefix("CS2040C") == "CS"


def test_module_prefix_multi_letter():
    assert module_prefix("GEA1000") == "GEA"


def test_module_prefix_unparseable():
    assert module_prefix("2100") is None


def test_module_level_basic():
    assert module_level("CS2100") == 2


def test_module_level_unparseable():
    assert module_level("???") is None


def test_level_label():
    assert level_label(2) == "2XXX"


def test_semester_labels_unique_sorted():
    assert semester_labels(_mods()) == ["Y1S1", "Y1S2", "Y2S1"]


def test_available_prefixes_dedup_sorted():
    assert available_prefixes(_mods()) == ["CS", "GEA", "MA"]


def test_available_levels_dedup_sorted():
    assert available_levels(_mods()) == [1, 2, 3]


def test_apply_filters_empty_state_returns_all():
    assert len(apply_filters(_mods(), FilterState())) == 5


def test_apply_filters_single_facet_semester():
    out = apply_filters(_mods(), FilterState(semesters=frozenset({"Y1S1"})))
    assert [m.module_code for m in out] == ["CS2100", "MA1521"]


def test_apply_filters_or_within_facet():
    out = apply_filters(
        _mods(), FilterState(semesters=frozenset({"Y1S1", "Y1S2"}))
    )
    assert [m.module_code for m in out] == ["CS2100", "CS2040C", "MA1521"]


def test_apply_filters_and_across_facets():
    out = apply_filters(
        _mods(), FilterState(prefixes=frozenset({"CS"}), levels=frozenset({2}))
    )
    assert [m.module_code for m in out] == ["CS2100", "CS2040C"]


def test_apply_filters_and_across_facets_no_match():
    out = apply_filters(
        _mods(), FilterState(prefixes=frozenset({"MA"}), levels=frozenset({2}))
    )
    assert out == []


def test_apply_filters_module_code_short_circuits_facets():
    out = apply_filters(
        _mods(),
        FilterState(prefixes=frozenset({"MA"}), module_code="CS2100"),
    )
    assert [m.module_code for m in out] == ["CS2100"]
