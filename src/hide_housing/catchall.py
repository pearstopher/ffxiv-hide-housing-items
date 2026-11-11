"""The "Miscellaneous" bulk group: whole-kind options that aren't one tab's categories.

Which things are covered always comes from datamined sheets. The model file
names are a *best guess*: their naming pattern was derived from the ResLogger2
path list, which the user approved for exactly these catch-alls (plant and food
model guesses) and nothing else. See docs/furniture-paths.md.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from hide_housing.meta import multi_group, option
from hide_housing.paths import model_paths
from hide_housing.sheets import read_sheet, to_bool

MISC_GROUP_NAME = "Miscellaneous"
MISC_GROUP_PRIORITY = 0

# --- Plants ---------------------------------------------------------------------
# Gardening models live in bgcommon/hou/outdoor/frm/{ModelID:04d}/bgparts/, where
# ModelID comes from the datamined GardeningSeed sheet. Pattern seen in the
# ResLogger2 list (668 files; every name fits it):
#   every seed:        frm_f{1-5}_m0{ID:03d}.mdl            (growth stages)
#   flowerpot seeds:   frm_f4_m{1-9}{ID:03d}.mdl, han_f4_m{0-9}{ID:03d}.mdl
GARDEN_DIR = "bgcommon/hou/outdoor/frm/{id:04d}/bgparts"
GROWTH_STAGES = range(1, 6)
POT_VARIANTS = range(0, 10)

PLANTS_OPTION_NAME = "All flowers and plants"
PLANTS_DESCRIPTION = "Hides all flowers and plants grown from seeds (best guess, may miss some)."


def load_garden_seeds(path: Path | str) -> dict[int, bool]:
    """``{ModelID: is a flowerpot seed}`` from the datamined GardeningSeed sheet."""
    seeds: dict[int, bool] = {}
    rows = read_sheet(path, {"Item": int, "ModelID": int, "IsPlantPotFlowerSeed": to_bool})
    for row in rows.values():
        if row["Item"] == 0 or row["ModelID"] == 0:
            continue
        seeds[row["ModelID"]] = seeds.get(row["ModelID"], False) or row["IsPlantPotFlowerSeed"]
    return seeds


def plant_model_paths(seeds: Mapping[int, bool]) -> list[str]:
    """Best-guess model paths for every gardening ModelID (see pattern above)."""
    paths: list[str] = []
    for model_id, is_pot_seed in sorted(seeds.items()):
        if not 1 <= model_id <= 999:
            continue  # names embed the id as three digits
        folder = GARDEN_DIR.format(id=model_id)
        names = [f"frm_f{stage}_m0{model_id:03d}.mdl" for stage in GROWTH_STAGES]
        if is_pot_seed:
            names += [f"frm_f4_m{v}{model_id:03d}.mdl" for v in POT_VARIANTS if v != 0]
            names += [f"han_f4_m{v}{model_id:03d}.mdl" for v in POT_VARIANTS]
        paths += [f"{folder}/{name}" for name in names]
    return paths


# --- Food -----------------------------------------------------------------------
# Food is furniture with HousingFurniture.UsageType 7 (datamined). Best guess per
# model: the main fun_b0_m{NNNN}.mdl plus "a" and "b" parts (food has two states:
# served and eaten), plus any extra parts in the saved multi-part list (#40).
FOOD_USAGE_TYPE = 7
FOOD_STATE_SUFFIXES = ("a", "b")

FOOD_OPTION_NAME = "All food"
FOOD_DESCRIPTION = "Hides all food and drink, served or eaten (best guess, may miss some)."


def load_food_model_keys(path: Path | str) -> list[int]:
    """Model keys of food furniture (UsageType 7) from the datamined HousingFurniture sheet."""
    rows = read_sheet(path, {"Item": int, "ModelKey": int, "UsageType": int})
    return sorted({
        row["ModelKey"] for row in rows.values()
        if row["Item"] and row["ModelKey"] and row["UsageType"] == FOOD_USAGE_TYPE
    })


def food_model_paths(model_keys: Iterable[int], parts: Mapping[int, Sequence[str]] | None = None) -> list[str]:
    """Best-guess model paths for every food model key."""
    parts = parts or {}
    paths: list[str] = []
    for key in model_keys:
        guesses = [f"fun_b0_m{key:04d}{suffix}.mdl" for suffix in FOOD_STATE_SUFFIXES]
        extras = sorted(set(guesses) | set(parts.get(key, ())))
        paths += model_paths(key, extras)
    return paths


# --- Effects (VFX) -----------------------------------------------------------
# Each housing effect is redirected to a game path that doesn't exist, so it
# fails to load and isn't drawn. That's the technique the EasyEyes plugin uses to
# remove effects; Penumbra's Resource Logger exempts this exact path from its
# load-failure warnings for that reason (Penumbra ResourceWatcher.cs).
NO_VFX_PATH = "vfx/path/nothing.avfx"
HOUSING_VFX_OPTION_NAME = "All housing effects"
# Stable option ID key (the option's first name, from #49).
HOUSING_VFX_OPTION_ID_KEY = "All indoor housing effects"
HOUSING_VFX_DESCRIPTION = (
    "Disables housing visual effects (VFX): every effect in the saved list from the indoor, "
    "dynamic, common and workshop housing effect folders (not outdoor), by redirecting it to a "
    "file that doesn't exist, the same technique the EasyEyes plugin uses. The list comes from the "
    "ResLogger2 game path list and may not be complete."
)


# --- Group ----------------------------------------------------------------------

Spec = tuple[str, list[str], str]  # (option name, game paths, description)


def catch_all_option_specs(
    garden_seeds_path: Path | str | None = None,
    furniture_path: Path | str | None = None,
    parts: Mapping[int, Sequence[str]] | None = None,
) -> list[Spec]:
    """Flowers/plants and food option specs, for whichever sheets are given."""
    specs: list[Spec] = []
    if garden_seeds_path is not None:
        plant_paths = plant_model_paths(load_garden_seeds(garden_seeds_path))
        if plant_paths:
            specs.append((PLANTS_OPTION_NAME, plant_paths, PLANTS_DESCRIPTION))
    if furniture_path is not None:
        food_paths = food_model_paths(load_food_model_keys(furniture_path), parts)
        if food_paths:
            specs.append((FOOD_OPTION_NAME, food_paths, FOOD_DESCRIPTION))
    return specs


def misc_groups(
    specs: Sequence[Spec],
    replacement: str,
    housing_vfx: Sequence[str] = (),
) -> list[dict[str, Any]]:
    """The "Miscellaneous" bulk group (all options off): one option per spec
    (model paths -> replacement), then one option disabling every housing VFX."""
    options = [
        option(MISC_GROUP_NAME, name, {path: replacement for path in paths}, description)
        for name, paths, description in specs
    ]
    if housing_vfx:
        options.append(option(
            MISC_GROUP_NAME, HOUSING_VFX_OPTION_NAME, {}, HOUSING_VFX_DESCRIPTION,
            id_key=HOUSING_VFX_OPTION_ID_KEY,
            file_swaps={path: NO_VFX_PATH for path in housing_vfx},
        ))
    if not options:
        return []
    return [multi_group(
        MISC_GROUP_NAME,
        options,
        MISC_GROUP_PRIORITY,
        "Hide whole kinds of things at once. Some lists are best guesses.",
    )]
