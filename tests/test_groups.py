from pathlib import Path

import pytest

from hide_housing import penumbra
from hide_housing.catalog import Catalog, FurnitureModel, Subcategory, TopLevel, load_catalog
from hide_housing.groups import category_groups, hide_files, split_multi_groups
from hide_housing.meta import ModInfo, build_meta, option
from hide_housing.paths import model_path

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHEETS = ("HousingFurniture", "FurnitureCatalogItemList", "FurnitureCatalogCategory", "Item")
REPLACEMENT = "files\\replacement.mdl"


def fixture_catalog():
    return load_catalog({name: FIXTURES / f"{name}.csv" for name in SHEETS})


def model(key, name="Thing"):
    return FurnitureModel(key, [(key, name)])


def test_hide_files_maps_every_model_to_replacement():
    assert hide_files([model(633), model(7)], REPLACEMENT) == {
        model_path(633): REPLACEMENT,
        model_path(7): REPLACEMENT,
    }


def test_category_groups_from_fixtures():
    groups = category_groups(fixture_catalog(), REPLACEMENT)
    assert [g["Name"] for g in groups] == [
        "Furnishings: hide whole categories",
        "Tables: hide whole categories",
        "Tabletop: hide whole categories",
    ]
    furnishings, tables, tabletop = groups
    (walls,) = furnishings["Options"]
    assert walls["Name"] == "Walls/Pillars/Partitions"
    assert walls["Files"] == {model_path(633): REPLACEMENT}
    assert walls["Description"] == "Hides all 1 furniture model in Furnishings > Walls/Pillars/Partitions."
    assert tabletop["Options"][0]["Name"] == "Other"
    assert tabletop["Options"][0]["Files"] == {model_path(290): REPLACEMENT}


def test_all_groups_multi_and_off_by_default():
    for group in category_groups(fixture_catalog(), REPLACEMENT):
        assert group["Type"] == "Multi"
        assert group["DefaultSettings"] == penumbra.ALL_OPTIONS_OFF


def test_repeated_subcategory_names_get_distinct_ids():
    tops = [
        TopLevel(12, "Furnishings", [Subcategory("Miscellaneous", 9, 10, [model(1)])]),
        TopLevel(14, "Tabletop", [Subcategory("Miscellaneous", 8, 15, [model(2)])]),
    ]
    groups = category_groups(Catalog(tops), REPLACEMENT)
    ids = [o["Id"] for g in groups for o in g["Options"]]
    assert len(set(ids)) == 2
    build_meta(ModInfo(), groups)  # passes the duplicate-ID check


def test_subcategory_with_only_invalid_models_is_left_out():
    tops = [TopLevel(12, "Furnishings", [
        Subcategory("Broken", 1, 1, [model(10000)]),
        Subcategory("Fine", 2, 2, [model(5)]),
    ])]
    (group,) = category_groups(Catalog(tops), REPLACEMENT)
    assert [o["Name"] for o in group["Options"]] == ["Fine"]


def test_many_categories_are_split_into_parts():
    subs = [Subcategory(f"Cat {i:02d}", i, i, [model(i + 1)]) for i in range(40)]
    groups = category_groups(Catalog([TopLevel(12, "Furnishings", subs)]), REPLACEMENT)
    assert [g["Name"] for g in groups] == [
        "Furnishings: hide whole categories, Part 1",
        "Furnishings: hide whole categories, Part 2",
    ]
    assert [len(g["Options"]) for g in groups] == [32, 8]


@pytest.mark.parametrize("count, sizes", [(0, [0]), (1, [1]), (32, [32]), (33, [32, 1]), (65, [32, 32, 1])])
def test_split_multi_groups_sizes(count, sizes):
    options = [option("G", f"O{i}", {}) for i in range(count)]
    groups = split_multi_groups("G", options)
    assert [len(g["Options"]) for g in groups] == sizes
    if len(sizes) == 1:
        assert groups[0]["Name"] == "G"


def test_split_keeps_option_ids_and_gives_parts_distinct_group_ids():
    options = [option("G", f"O{i}", {}) for i in range(33)]
    groups = split_multi_groups("G", options)
    assert groups[1]["Options"][0]["Id"] == options[32]["Id"]
    assert groups[0]["Id"] != groups[1]["Id"]
