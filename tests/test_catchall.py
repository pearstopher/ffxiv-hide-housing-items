from pathlib import Path

from hide_housing import penumbra
from hide_housing.catchall import (
    FOOD_DESCRIPTION,
    FOOD_OPTION_NAME,
    HOUSING_VFX_OPTION_NAME,
    MISC_GROUP_NAME,
    NO_VFX_PATH,
    PLANTS_DESCRIPTION,
    PLANTS_OPTION_NAME,
    catch_all_option_specs,
    food_model_paths,
    load_food_model_keys,
    load_garden_seeds,
    misc_groups,
    plant_model_paths,
)
from hide_housing.meta import stable_id
from hide_housing.parts import extract_housing_vfx, load_housing_vfx

FIXTURES = Path(__file__).resolve().parent / "fixtures"
REPLACEMENT = "files\\replacement.mdl"
FRM = "bgcommon/hou/outdoor/frm"

# Paths the user captured in game with Penumbra's Resource Logger (#41).
CAPTURED = [
    f"{FRM}/0106/bgparts/han_f4_m0106.mdl",  # Red Cherry Blossoms (flowerpot)
    f"{FRM}/0102/bgparts/han_f4_m8102.mdl",  # Purple Violas (flowerpot)
    f"{FRM}/0006/bgparts/frm_f4_m0006.mdl",  # shards (planted crystals)
]


# --- plants (#41) -----------------------------------------------------------------

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


def test_shipped_fixture_has_no_food_so_no_food_option():
    assert catch_all_option_specs(None, FIXTURES / "HousingFurniture.csv") == []


def test_plant_and_food_descriptions_are_one_short_sentence():
    for description in (PLANTS_DESCRIPTION, FOOD_DESCRIPTION):
        assert description.count(". ") == 0 and description.endswith(".")
        assert "best guess" in description
        assert len(description) <= 100


# --- housing VFX (#49, #51) ---------------------------------------------------------

COMMON = "bgcommon/hou/common"
VFX = f"{COMMON}/vfx_hou_ind1/eff"
INCLUDED = ("vfx_hou_ind1", "vfx_hou_dyna1", "vfx_hou_com1", "vfx_hou_craft1")


def test_extract_housing_vfx_takes_four_folders_but_not_outdoor():
    lines = [
        f"{VFX}/i_fire0001_o.avfx",
        f"{VFX}/i_fire0001_o.avfx",
        f"{VFX}/i_fire0001_o.atex",
        f"{COMMON}/vfx_hou_out1/eff/o_fire0001_o.avfx",
        f"{COMMON}/vfx_hou_com1/eff/bl_stop01l_o.avfx",
        f"{COMMON}/vfx_hou_dyna1/eff/d_x.avfx",
        f"{COMMON}/vfx_hou_craft1/eff/c_x.avfx",
        f"{COMMON}/vfx_hou_ind10/eff/not_a_match.avfx",
    ]
    assert extract_housing_vfx(lines) == [
        f"{COMMON}/vfx_hou_com1/eff/bl_stop01l_o.avfx",
        f"{COMMON}/vfx_hou_craft1/eff/c_x.avfx",
        f"{COMMON}/vfx_hou_dyna1/eff/d_x.avfx",
        f"{VFX}/i_fire0001_o.avfx",
    ]


def test_shipped_housing_vfx_list():
    vfx = load_housing_vfx()
    assert vfx == sorted(set(vfx))
    assert all(p.endswith(".avfx") for p in vfx)
    assert {p.split("/")[3] for p in vfx} == set(INCLUDED)
    assert len([p for p in vfx if "/vfx_hou_ind1/" in p]) >= 200


# --- Miscellaneous group (#53) ------------------------------------------------------

def test_misc_group_has_one_bulk_option_each_in_order_all_off(tmp_path):
    rugs = ("All rugs", [f"{GENERAL}/0001/bgparts/fun_b0_m0001.mdl"], "Hides all rugs.")
    specs = [rugs] + catch_all_option_specs(FIXTURES / "GardeningSeed.csv", write_furniture(tmp_path))
    (group,) = misc_groups(specs, REPLACEMENT, [f"{VFX}/a.avfx", f"{VFX}/b.avfx"])
    assert group["Name"] == MISC_GROUP_NAME == "Miscellaneous"
    assert group["Type"] == "Multi" and group["DefaultSettings"] == penumbra.ALL_OPTIONS_OFF
    names = [o["Name"] for o in group["Options"]]
    assert names == ["All rugs", PLANTS_OPTION_NAME, FOOD_OPTION_NAME, HOUSING_VFX_OPTION_NAME]

    plants, food, effects = group["Options"][1:]
    assert set(CAPTURED) <= set(plants["Files"]) and set(plants["Files"].values()) == {REPLACEMENT}
    assert len(food["Files"]) == 2 * 3
    assert effects["Files"] == {}
    assert effects["FileSwaps"] == {f"{VFX}/a.avfx": NO_VFX_PATH, f"{VFX}/b.avfx": NO_VFX_PATH}
    assert effects["Id"] == stable_id("option", MISC_GROUP_NAME, "All indoor housing effects")


def test_misc_group_needs_something_to_hold():
    assert misc_groups([], REPLACEMENT) == []
    assert catch_all_option_specs(None) == []
