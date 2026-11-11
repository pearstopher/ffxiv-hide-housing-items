from pathlib import Path

from hide_housing import penumbra
from hide_housing.catalog import load_catalog
from hide_housing.catchall import (
    CATCH_ALL_GROUP_NAME,
    EFFECTS_GROUP_NAME,
    FOOD_OPTION_NAME,
    NO_VFX_PATH,
    PLANTS_OPTION_NAME,
    catch_all_groups,
    catch_all_option_specs,
    effects_groups,
    food_model_paths,
    load_food_model_keys,
    load_garden_seeds,
    plant_model_paths,
)
from hide_housing.groups import all_groups
from hide_housing.meta import ModInfo, build_meta
from hide_housing.parts import extract_indoor_vfx, load_indoor_vfx

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


# --- food (#44) -------------------------------------------------------------------

GENERAL = "bgcommon/hou/indoor/general"
FURNITURE_CSV = (
    "#,UsageParameter,CustomTalk,Item,ModelKey,HousingItemCategory,UsageType,PlaceLimitType,"
    "AquariumTier,Placement,Unplacement,UnplacementStorage,DestroyOnRemoval,Unknown4,Unknown5,Unknown6\n"
    "196608,0,0,0,0,0,0,0,0,0,0,0,False,False,False,False\n"
    "196609,0,0,6601,1,13,0,0,0,0,0,0,False,False,True,False\n"       # table: not food
    "196857,1,0,8000,249,14,7,0,0,0,0,0,False,False,True,False\n"     # Gourmet Lunch: food
    "196858,22,0,8001,219,14,7,0,0,0,0,0,False,False,True,False\n"    # High House Supper Set: food
    "196859,2,0,0,250,14,7,0,0,0,0,0,False,False,False,False\n"       # unused row: skipped
)


def write_furniture(tmp_path):
    path = tmp_path / "HousingFurniture.csv"
    path.write_bytes(FURNITURE_CSV.encode())
    return path


def test_food_keys_come_from_datamined_usage_type(tmp_path):
    assert load_food_model_keys(write_furniture(tmp_path)) == [219, 249]


def test_food_paths_main_plus_both_states_plus_saved_parts():
    paths = food_model_paths([249, 253], {253: ["fun_b0_m0253c.mdl"]})
    assert paths == [
        f"{GENERAL}/0249/bgparts/fun_b0_m0249.mdl",
        f"{GENERAL}/0249/bgparts/fun_b0_m0249a.mdl",
        f"{GENERAL}/0249/bgparts/fun_b0_m0249b.mdl",
        f"{GENERAL}/0253/bgparts/fun_b0_m0253.mdl",
        f"{GENERAL}/0253/bgparts/fun_b0_m0253a.mdl",
        f"{GENERAL}/0253/bgparts/fun_b0_m0253b.mdl",
        f"{GENERAL}/0253/bgparts/fun_b0_m0253c.mdl",
    ]


def test_catch_all_group_has_plants_and_food_and_nothing_individual(tmp_path):
    specs = catch_all_option_specs(FIXTURES / "GardeningSeed.csv", write_furniture(tmp_path))
    (group,) = catch_all_groups(specs, REPLACEMENT)
    assert [o["Name"] for o in group["Options"]] == [PLANTS_OPTION_NAME, FOOD_OPTION_NAME]
    food = group["Options"][1]
    assert "may not catch every model" in food["Description"]
    assert len(food["Files"]) == 2 * 3
    assert group["DefaultSettings"] == penumbra.ALL_OPTIONS_OFF


def test_shipped_fixture_has_no_food_so_no_food_option():
    specs = catch_all_option_specs(None, FIXTURES / "HousingFurniture.csv")
    assert specs == []


# --- indoor VFX (#49) ---------------------------------------------------------------

VFX = "bgcommon/hou/common/vfx_hou_ind1/eff"


def test_extract_indoor_vfx_only_vfx_hou_ind1_avfx():
    lines = [
        f"{VFX}/i_fire0001_o.avfx",
        f"{VFX}/i_fire0001_o.avfx",
        f"{VFX}/i_fire0001_o.atex",
        "bgcommon/hou/common/vfx_hou_out1/eff/o_fire0001_o.avfx",
        "bgcommon/hou/common/vfx_hou_com1/eff/bl_stop01l_o.avfx",
        f"{VFX}/a_light001_y.avfx",
    ]
    assert extract_indoor_vfx(lines) == [f"{VFX}/a_light001_y.avfx", f"{VFX}/i_fire0001_o.avfx"]


def test_shipped_indoor_vfx_list():
    vfx = load_indoor_vfx()
    assert len(vfx) >= 200
    assert vfx == sorted(set(vfx))
    assert all(p.startswith("bgcommon/hou/common/vfx_hou_ind1/") and p.endswith(".avfx") for p in vfx)


def test_effects_group_is_one_bulk_option_using_file_swaps():
    (group,) = effects_groups([f"{VFX}/a.avfx", f"{VFX}/b.avfx"])
    assert group["Name"] == EFFECTS_GROUP_NAME
    assert group["Type"] == "Multi" and group["DefaultSettings"] == penumbra.ALL_OPTIONS_OFF
    (opt,) = group["Options"]
    assert opt["Files"] == {}
    assert opt["FileSwaps"] == {f"{VFX}/a.avfx": NO_VFX_PATH, f"{VFX}/b.avfx": NO_VFX_PATH}
    assert "may not be complete" in opt["Description"]


def test_no_effects_group_without_vfx():
    assert effects_groups([]) == []
