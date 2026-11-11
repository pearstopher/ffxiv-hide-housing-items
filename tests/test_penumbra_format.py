"""Check the generated meta.json against the Penumbra rules in docs/penumbra-format.md."""

from pathlib import Path, PureWindowsPath

from hide_housing import penumbra
from hide_housing.assets import bundle_replacement
from hide_housing.catalog import load_catalog
from hide_housing.groups import all_groups, item_groups
from hide_housing.meta import ModInfo, build_meta

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHEETS = ("HousingFurniture", "FurnitureCatalogItemList", "FurnitureCatalogCategory", "Item")


def generated_meta(build_dir):
    replacement = bundle_replacement(build_dir)
    catalog = load_catalog({name: FIXTURES / f"{name}.csv" for name in SHEETS})
    groups = all_groups(catalog, replacement) or item_groups(catalog, replacement)
    return build_meta(ModInfo(), groups)


def test_constants():
    assert penumbra.FILE_VERSION == 4
    assert penumbra.MAX_MULTI_OPTIONS == 32
    assert penumbra.ALL_OPTIONS_OFF == 0


def test_uses_current_file_version_with_inline_groups(tmp_path):
    meta = generated_meta(tmp_path)
    assert meta["FileVersion"] == penumbra.FILE_VERSION
    assert meta["Name"]
    assert isinstance(meta["Groups"], list) and meta["Groups"]


def test_groups_respect_multi_option_limit_and_start_off(tmp_path):
    for group in generated_meta(tmp_path)["Groups"]:
        assert group["Type"] == "Multi"
        assert len(group["Options"]) <= penumbra.MAX_MULTI_OPTIONS
        assert group["DefaultSettings"] == penumbra.ALL_OPTIONS_OFF


def test_file_redirections_use_forward_slash_game_paths_and_shipped_files(tmp_path):
    meta = generated_meta(tmp_path)
    containers = [meta["DefaultData"]] + [o for g in meta["Groups"] for o in g["Options"]]
    assert meta["DefaultData"]["Files"] == {}
    for container in containers:
        for game_path, mod_path in container.get("Files", {}).items():
            assert "\\" not in game_path and not game_path.startswith("/")
            assert (tmp_path / PureWindowsPath(mod_path).as_posix()).is_file()
