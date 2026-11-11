from pathlib import Path

from hide_housing import penumbra
from hide_housing.catalog import load_catalog
from hide_housing.catchall import (
    CATCH_ALL_GROUP_NAME,
    PLANTS_OPTION_NAME,
    catch_all_groups,
    catch_all_option_specs,
    load_garden_seeds,
    plant_model_paths,
)
from hide_housing.groups import all_groups
from hide_housing.meta import ModInfo, build_meta

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHEETS = ("HousingFurniture", "FurnitureCatalogItemList", "FurnitureCatalogCategory", "Item")
REPLACEMENT = "files\\replacement.mdl"
FRM = "bgcommon/hou/outdoor/frm"

# Paths the user captured in game with Penumbra's Resource Logger (#41).
CAPTURED = [
    f"{FRM}/0106/bgparts/han_f4_m0106.mdl",  # Red Cherry Blossoms (flowerpot)
    f"{FRM}/0102/bgparts/han_f4_m8102.mdl",  # Purple Violas (flowerpot)
    f"{FRM}/0006/bgparts/frm_f4_m0006.mdl",  # shards (planted crystals)
]


def test_load_garden_seeds_from_datamined_fixture():
    assert load_garden_seeds(FIXTURES / "GardeningSeed.csv") == {1: False, 6: False, 102: True, 106: True}


def test_plant_paths_cover_everything_captured_in_game():
    paths = plant_model_paths(load_garden_seeds(FIXTURES / "GardeningSeed.csv"))
    for path in CAPTURED:
        assert path in paths


def test_plant_path_pattern_counts():
    paths = plant_model_paths({6: False, 102: True})
    shard = [p for p in paths if "/0006/" in p]
    violas = [p for p in paths if "/0102/" in p]
    assert shard == [f"{FRM}/0006/bgparts/frm_f{s}_m0006.mdl" for s in range(1, 6)]
    assert len(violas) == 5 + 9 + 10  # growth stages + frm_f4 variants + han_f4 variants
    assert len(set(paths)) == len(paths)


def test_plant_ids_outside_three_digits_are_skipped():
    assert plant_model_paths({1000: True, 0: False}) == []


def test_catch_all_group_has_single_plants_option_off_by_default():
    specs = catch_all_option_specs(FIXTURES / "GardeningSeed.csv")
    (group,) = catch_all_groups(specs, REPLACEMENT)
    assert group["Name"] == CATCH_ALL_GROUP_NAME
    assert group["Type"] == "Multi" and group["DefaultSettings"] == penumbra.ALL_OPTIONS_OFF
    (plants,) = group["Options"]
    assert plants["Name"] == PLANTS_OPTION_NAME
    assert "may not catch every model" in plants["Description"]
    assert set(plants["Files"].values()) == {REPLACEMENT}
    assert set(CAPTURED) <= set(plants["Files"])


def test_no_individual_flower_options_and_bulk_groups_come_first():
    catalog = load_catalog({name: FIXTURES / f"{name}.csv" for name in SHEETS})
    catch_all = catch_all_groups(catch_all_option_specs(FIXTURES / "GardeningSeed.csv"), REPLACEMENT)
    groups = all_groups(catalog, REPLACEMENT, catch_all=catch_all)
    names = [g["Name"] for g in groups]
    assert names[:4] == [
        "Furnishings: hide whole categories",
        "Tables: hide whole categories",
        "Tabletop: hide whole categories",
        CATCH_ALL_GROUP_NAME,
    ]
    garden_options = [o for g in groups for o in g["Options"] if any("/outdoor/frm/" in p for p in o["Files"])]
    assert [o["Name"] for o in garden_options] == [PLANTS_OPTION_NAME]
    build_meta(ModInfo(), groups)


def test_no_catch_all_without_data():
    assert catch_all_option_specs(None) == []
    assert catch_all_groups([], REPLACEMENT) == []
