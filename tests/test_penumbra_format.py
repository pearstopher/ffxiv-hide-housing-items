"""Check the documented Penumbra rules against the known-working example mod."""

import json
from pathlib import Path

from hide_housing import penumbra

EXAMPLE = Path(__file__).resolve().parent.parent / "example"


def load_example_meta():
    return json.loads((EXAMPLE / "meta.json").read_text(encoding="utf-8"))


def test_constants():
    assert penumbra.FILE_VERSION == 4
    assert penumbra.MAX_MULTI_OPTIONS == 32
    assert penumbra.ALL_OPTIONS_OFF == 0


def test_example_uses_current_file_version_with_inline_groups():
    meta = load_example_meta()
    assert meta["FileVersion"] == penumbra.FILE_VERSION
    assert meta["Name"]
    assert isinstance(meta["Groups"], list)


def test_example_groups_respect_multi_option_limit():
    for group in load_example_meta()["Groups"]:
        if group["Type"] == "Multi":
            assert len(group["Options"]) <= penumbra.MAX_MULTI_OPTIONS


def test_example_file_redirections_point_at_shipped_files():
    meta = load_example_meta()
    containers = [meta["DefaultData"]] + [
        option for group in meta["Groups"] for option in group["Options"]
    ]
    for container in containers:
        for game_path, mod_path in container.get("Files", {}).items():
            assert "\\" not in game_path and not game_path.startswith("/")
            assert (EXAMPLE / mod_path.replace("\\", "/")).is_file()
