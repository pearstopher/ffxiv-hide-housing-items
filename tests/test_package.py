import json
import zipfile
from pathlib import Path, PureWindowsPath

import pytest

from hide_housing.assets import bundle_replacement
from hide_housing.catalog import load_catalog
from hide_housing.groups import all_groups
from hide_housing.meta import ModInfo, build_meta, write_meta
from hide_housing.package import PackageError, package_mod, pmp_filename, referenced_files

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHEETS = ("HousingFurniture", "FurnitureCatalogItemList", "FurnitureCatalogCategory", "Item")


def make_build(build_dir, info=ModInfo()):
    replacement = bundle_replacement(build_dir)
    catalog = load_catalog({name: FIXTURES / f"{name}.csv" for name in SHEETS})
    write_meta(build_dir, build_meta(info, all_groups(catalog, replacement)))
    return build_dir


def test_pmp_contents_are_valid_and_complete(tmp_path):
    pmp = package_mod(make_build(tmp_path / "build"), tmp_path / "dist")
    assert pmp == tmp_path / "dist" / "hide-housing-furniture-0.1.0.pmp"

    with zipfile.ZipFile(pmp) as archive:
        names = set(archive.namelist())
        assert names == {"meta.json", "files/replacement.mdl"}
        json_files = [n for n in names if n.endswith(".json")]
        parsed = {n: json.loads(archive.read(n).decode("utf-8")) for n in json_files}

    meta = parsed["meta.json"]
    assert meta["FileVersion"] == 4 and meta["Groups"]
    referenced = {
        PureWindowsPath(p).as_posix()
        for g in meta["Groups"] for o in g["Options"] for p in o["Files"].values()
    }
    assert referenced == {"files/replacement.mdl"}
    assert referenced <= names


def test_rebuild_gives_identical_archive(tmp_path):
    first = package_mod(make_build(tmp_path / "a"), tmp_path / "d1").read_bytes()
    second = package_mod(make_build(tmp_path / "b"), tmp_path / "d2").read_bytes()
    assert first == second


def test_overwrites_existing_and_leaves_no_partial(tmp_path):
    build = make_build(tmp_path / "build")
    pmp = package_mod(build, tmp_path / "dist")
    pmp.write_bytes(b"stale")
    package_mod(build, tmp_path / "dist")
    assert zipfile.is_zipfile(pmp)
    assert [p.name for p in (tmp_path / "dist").iterdir()] == [pmp.name]


def test_missing_meta(tmp_path):
    (tmp_path / "build").mkdir()
    with pytest.raises(PackageError, match="meta.json not found"):
        package_mod(tmp_path / "build", tmp_path / "dist")


def test_invalid_json(tmp_path):
    build = tmp_path / "build"
    build.mkdir()
    (build / "meta.json").write_text("{nope", encoding="utf-8")
    with pytest.raises(PackageError, match="not valid JSON"):
        package_mod(build, tmp_path / "dist")


def test_missing_referenced_file_is_rejected(tmp_path):
    build = make_build(tmp_path / "build")
    (build / "files" / "replacement.mdl").unlink()
    with pytest.raises(PackageError, match="files/replacement.mdl"):
        package_mod(build, tmp_path / "dist")
    assert not (tmp_path / "dist").exists() or not any((tmp_path / "dist").iterdir())


def test_referenced_files_normalises_backslashes():
    meta = {
        "DefaultData": {"Files": {"a/b.mdl": "files\\x.mdl"}},
        "Groups": [{"Options": [{"Files": {"c/d.mdl": "files\\sub\\y.mdl"}}, {"Files": None}]}],
    }
    assert referenced_files(meta) == {"files/x.mdl", "files/sub/y.mdl"}


@pytest.mark.parametrize("name, version, expected", [
    ("Hide Housing Furniture", "0.1.0", "hide-housing-furniture-0.1.0.pmp"),
    ("  Weird/Name: v2!  ", "1.0 beta", "weird-name-v2-1.0-beta.pmp"),
    ("", "", "mod-0.pmp"),
])
def test_pmp_filename(name, version, expected):
    assert pmp_filename(name, version) == expected
