import hashlib

import pytest

from hide_housing.assets import bundle_replacement, default_replacement

# The tiny model made in Blender and confirmed working in game (#15).
TESTED_MODEL_SHA256 = "89f0438b339e5a9b6e9362563250d23e30a9a7db475193307444e651cdafed78"


def test_default_replacement_is_the_tested_tiny_model():
    default = default_replacement().read_bytes()
    assert hashlib.sha256(default).hexdigest() == TESTED_MODEL_SHA256
    assert len(default) == 830
    assert default[:4] == (0x01000006).to_bytes(4, "little")  # .mdl version 6 header


def test_copies_default_into_files_dir(tmp_path):
    mod_path = bundle_replacement(tmp_path)
    assert mod_path == "files\\replacement.mdl"
    copied = tmp_path / "files" / "replacement.mdl"
    assert copied.read_bytes() == default_replacement().read_bytes()
    assert [p.name for p in tmp_path.rglob("*") if p.is_file()] == ["replacement.mdl"]


def test_custom_source(tmp_path):
    custom = tmp_path / "invisible.mdl"
    custom.write_bytes(b"\x00custom")
    build = tmp_path / "build"
    mod_path = bundle_replacement(build, source=custom)
    assert (build / mod_path.replace("\\", "/")).read_bytes() == b"\x00custom"


def test_overwrites_previous_build(tmp_path):
    (tmp_path / "files").mkdir()
    (tmp_path / "files" / "replacement.mdl").write_bytes(b"old")
    bundle_replacement(tmp_path)
    assert (tmp_path / "files" / "replacement.mdl").read_bytes() != b"old"


def test_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError, match="nope.mdl"):
        bundle_replacement(tmp_path, source=tmp_path / "nope.mdl")


def test_rejects_non_mdl(tmp_path):
    tex = tmp_path / "a.tex"
    tex.write_bytes(b"x")
    with pytest.raises(ValueError, match=r"\.mdl"):
        bundle_replacement(tmp_path / "build", source=tex)
