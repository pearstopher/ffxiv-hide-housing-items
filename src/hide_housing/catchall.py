"""Catch-all bulk options for things that aren't ordinary furniture models.

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

CATCH_ALL_GROUP_NAME = "Catch-all: hide whole categories"
CATCH_ALL_GROUP_PRIORITY = 0
BEST_GUESS_NOTE = "Best guess: this may not catch every model, or may include a few that don't exist."

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
PLANTS_DESCRIPTION = (
    "Hides everything grown from gardening seeds: flowers in flowerpots, crops and planted "
    "shards. Garden plots outdoors use the same models, so they may be hidden there too. "
    + BEST_GUESS_NOTE
)


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
FOOD_DESCRIPTION = "Hides every food and drink furniture item, served or eaten. " + BEST_GUESS_NOTE


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
# Each indoor housing effect is redirected to a game path that doesn't exist, so it
# fails to load and isn't drawn. That's the technique the EasyEyes plugin uses to
# remove effects; Penumbra's Resource Logger exempts this exact path from its
# load-failure warnings for that reason (Penumbra ResourceWatcher.cs).
NO_VFX_PATH = "vfx/path/nothing.avfx"
EFFECTS_GROUP_NAME = "Effects: disable all"
EFFECTS_GROUP_PRIORITY = 0
INDOOR_VFX_OPTION_NAME = "All indoor housing effects"
INDOOR_VFX_DESCRIPTION = (
    "Disables every indoor housing visual effect (VFX) in the saved list by redirecting it to a "
    "file that doesn't exist, the same technique the EasyEyes plugin uses. The list comes from the "
    "ResLogger2 game path list and may not be complete."
)


def effects_groups(indoor_vfx: Sequence[str]) -> list[dict[str, Any]]:
    """One Multi group with a single option that disables every listed indoor VFX."""
    if not indoor_vfx:
        return []
    swaps = {path: NO_VFX_PATH for path in indoor_vfx}
    return [multi_group(
        EFFECTS_GROUP_NAME,
        [option(EFFECTS_GROUP_NAME, INDOOR_VFX_OPTION_NAME, {}, INDOOR_VFX_DESCRIPTION, file_swaps=swaps)],
        EFFECTS_GROUP_PRIORITY,
        "Turn off housing visual effects.",
    )]


# --- Group ----------------------------------------------------------------------

def catch_all_option_specs(
    garden_seeds_path: Path | str | None = None,
    furniture_path: Path | str | None = None,
    parts: Mapping[int, Sequence[str]] | None = None,
) -> list[tuple[str, list[str], str]]:
    """``[(option name, game paths, description)]`` for every catch-all with data."""
    specs: list[tuple[str, list[str], str]] = []
    if garden_seeds_path is not None:
        plant_paths = plant_model_paths(load_garden_seeds(garden_seeds_path))
        if plant_paths:
            specs.append((PLANTS_OPTION_NAME, plant_paths, PLANTS_DESCRIPTION))
    if furniture_path is not None:
        food_paths = food_model_paths(load_food_model_keys(furniture_path), parts)
        if food_paths:
            specs.append((FOOD_OPTION_NAME, food_paths, FOOD_DESCRIPTION))
    return specs


def catch_all_groups(specs: list[tuple[str, list[str], str]], replacement: str) -> list[dict[str, Any]]:
    """One Multi group (all options off) with an option per catch-all."""
    options = [
        option(CATCH_ALL_GROUP_NAME, name, {path: replacement for path in paths}, description)
        for name, paths, description in specs
    ]
    if not options:
        return []
    return [multi_group(
        CATCH_ALL_GROUP_NAME,
        options,
        CATCH_ALL_GROUP_PRIORITY,
        "Hide whole kinds of things that aren't single furniture items. Best-guess lists.",
    )]
