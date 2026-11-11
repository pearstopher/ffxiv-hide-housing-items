import json
import uuid

import pytest

from hide_housing import penumbra
from hide_housing.meta import ModInfo, build_meta, multi_group, option, stable_id, write_meta

STAGE_PANEL = {"bgcommon/hou/indoor/general/0633/bgparts/fun_b0_m0633.mdl": "files\\replacement.mdl"}


def sample_groups():
    return [multi_group("Furnishings – Walls/Pillars/Partitions", [
        option("Furnishings – Walls/Pillars/Partitions", "Stage Panel", STAGE_PANEL),
    ])]


def test_meta_fields_and_file_version():
    info = ModInfo(name="Test Mod", author="Someone", description="Desc", version="1.2", website="https://x")
    meta = build_meta(info)
    assert meta["FileVersion"] == penumbra.FILE_VERSION == 4
    assert (meta["Name"], meta["Author"], meta["Description"], meta["Version"], meta["Website"]) == (
        "Test Mod", "Someone", "Desc", "1.2", "https://x"
    )
    uuid.UUID(meta["Identifier"])


def test_default_author_matches_example():
    assert ModInfo().author == "Ane Mora"
    assert build_meta(ModInfo())["Author"] == "Ane Mora"


def test_default_data_replaces_nothing():
    meta = build_meta(ModInfo(), sample_groups())
    assert meta["DefaultData"] == {"Files": {}, "FileSwaps": {}, "Manipulations": []}


def test_groups_are_multi_and_off_by_default():
    (group,) = build_meta(ModInfo(), sample_groups())["Groups"]
    assert group["Type"] == "Multi"
    assert group["DefaultSettings"] == 0
    assert group["Options"][0]["Files"] == STAGE_PANEL


def test_ids_are_deterministic_and_distinct():
    assert stable_id("group", "A") == stable_id("group", "A")
    assert stable_id("group", "A") != stable_id("option", "A")
    # parts are joined with a separator, so ("ab", "c") != ("a", "bc")
    assert stable_id("ab", "c") != stable_id("a", "bc")
    uuid.UUID(stable_id("x"))
    # same option name in different groups gets different IDs
    assert option("G1", "Lamp", {})["Id"] != option("G2", "Lamp", {})["Id"]


def test_rebuild_writes_identical_file(tmp_path):
    first = write_meta(tmp_path / "a", build_meta(ModInfo(), sample_groups())).read_bytes()
    second = write_meta(tmp_path / "b", build_meta(ModInfo(), sample_groups())).read_bytes()
    assert first == second


def test_written_file_is_valid_utf8_json_with_backslash_paths(tmp_path):
    path = write_meta(tmp_path, build_meta(ModInfo(), sample_groups()))
    assert path.name == "meta.json"
    raw = path.read_text(encoding="utf-8")
    assert "Furnishings – Walls" in raw  # en dash kept as UTF-8, not \u escaped
    assert '"files\\\\replacement.mdl"' in raw  # JSON-escaped backslash, as Penumbra writes it
    assert json.loads(raw)["Groups"][0]["Options"][0]["Files"] == STAGE_PANEL


def test_group_rejects_too_many_options():
    options = [option("G", f"Item {i}", {}) for i in range(penumbra.MAX_MULTI_OPTIONS + 1)]
    with pytest.raises(ValueError, match="33 options"):
        multi_group("G", options)
    multi_group("G", options[:-1])  # exactly 32 is fine


def test_duplicate_ids_rejected():
    group = multi_group("G", [option("G", "Same", {}), option("G", "Same", {})])
    with pytest.raises(ValueError, match="Duplicate"):
        build_meta(ModInfo(), [group])


def test_empty_name_rejected():
    with pytest.raises(ValueError, match="name"):
        build_meta(ModInfo(name="  "))
