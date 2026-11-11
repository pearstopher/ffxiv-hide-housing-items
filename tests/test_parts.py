import gzip
import json

import pytest

from hide_housing import parts as parts_mod
from hide_housing.download import DownloadError
from hide_housing.groups import hide_files
from hide_housing.catalog import FurnitureModel
from hide_housing.parts import PATH_LIST_URL, extract_parts, load_parts, refresh_parts
from hide_housing.paths import model_path, model_paths

GENERAL = "bgcommon/hou/indoor/general"
PATH_LIST = "\n".join([
    "common/font/font_krn_2.tex",
    f"{GENERAL}/0405/asset/fun_b0_m0405.sgb",
    f"{GENERAL}/0405/bgparts/fun_b0_m0405.mdl",
    f"{GENERAL}/0405/bgparts/fun_b0_m0405a.mdl",
    f"{GENERAL}/0405/texture/fun_b0_m0405_0a_d.tex",
    f"{GENERAL}/0974/bgparts/fun_b0_m0974b.mdl",
    f"{GENERAL}/0974/bgparts/fun_b0_m0974a.mdl",
    f"{GENERAL}/0974/bgparts/fun_b0_m0974a.mdl",  # duplicates are fine
    f"{GENERAL}/0413/bgparts/bds_t4_m0413.mdl",
    f"{GENERAL}/0443/bgparts/fun_b0_m0443.mdl",  # main model only -> not listed
    "bgcommon/hou/outdoor/general/0001/bgparts/gar_b0_m0001a.mdl",  # outdoor -> ignored
    f"{GENERAL}/0001/bgparts/sub/fun_b0_m0001a.mdl",  # nested -> ignored
]) + "\n"


def gz(text):
    return gzip.compress(text.encode("utf-8"))


# --- extraction ---------------------------------------------------------------

def test_extract_parts_keeps_only_extra_bgparts_models():
    assert extract_parts(PATH_LIST.splitlines()) == {
        405: ["fun_b0_m0405a.mdl"],
        413: ["bds_t4_m0413.mdl"],
        974: ["fun_b0_m0974a.mdl", "fun_b0_m0974b.mdl"],
    }


# --- saved file ---------------------------------------------------------------

def test_shipped_parts_list_has_the_door_leaf_found_in_research():
    shipped = load_parts()
    assert shipped[405] == ["fun_b0_m0405a.mdl"]  # Mahogany Partition Door
    assert len(shipped) >= 300
    for key, names in shipped.items():
        assert names == sorted(names) and all(n.endswith(".mdl") and "/" not in n for n in names)
        assert f"fun_b0_m{key:04d}.mdl" not in names


def test_load_missing_file_explains_how_to_create_it(tmp_path):
    with pytest.raises(FileNotFoundError, match="--refresh-parts"):
        load_parts(tmp_path / "nope.json")


def test_load_invalid_file(tmp_path):
    bad = tmp_path / "parts.json"
    bad.write_text('{"parts": ["not", "a", "dict"]}', encoding="utf-8")
    with pytest.raises(ValueError, match="invalid"):
        load_parts(bad)


# --- refresh --------------------------------------------------------------------

@pytest.fixture
def fake_download(monkeypatch):
    calls = []

    def fetch(url):
        calls.append(url)
        return gz(PATH_LIST)

    monkeypatch.setattr(parts_mod, "_fetch", fetch)
    return calls


def test_refresh_creates_saved_file(tmp_path, fake_download):
    saved = tmp_path / "data" / "model_parts.json"
    parts, changed = refresh_parts(saved)
    assert changed and fake_download == [PATH_LIST_URL]
    data = json.loads(saved.read_text(encoding="utf-8"))
    assert data["source"] == PATH_LIST_URL
    assert data["parts"]["0405"] == ["fun_b0_m0405a.mdl"]
    assert load_parts(saved) == parts


def test_refresh_leaves_unchanged_file_untouched(tmp_path, fake_download):
    saved = tmp_path / "model_parts.json"
    refresh_parts(saved)
    before = saved.stat().st_mtime_ns
    saved.write_text(saved.read_text(encoding="utf-8"), encoding="utf-8")  # same content
    mtime = saved.stat().st_mtime_ns
    _, changed = refresh_parts(saved)
    assert not changed
    assert saved.stat().st_mtime_ns == mtime
    assert before <= mtime


def test_refresh_rewrites_when_parts_change(tmp_path, fake_download):
    saved = tmp_path / "model_parts.json"
    saved.write_text(json.dumps({"parts": {"0405": ["old.mdl"]}}), encoding="utf-8")
    _, changed = refresh_parts(saved)
    assert changed
    assert load_parts(saved)[405] == ["fun_b0_m0405a.mdl"]


def test_refresh_rejects_bad_download_and_keeps_saved_file(tmp_path, monkeypatch):
    saved = tmp_path / "model_parts.json"
    saved.write_text(json.dumps({"parts": {"0405": ["fun_b0_m0405a.mdl"]}}), encoding="utf-8")
    original = saved.read_text(encoding="utf-8")

    monkeypatch.setattr(parts_mod, "_fetch", lambda url: b"not gzip")
    with pytest.raises(DownloadError, match="Could not read"):
        refresh_parts(saved)

    monkeypatch.setattr(parts_mod, "_fetch", lambda url: gz("common/nothing.tex\n"))
    with pytest.raises(DownloadError, match="no furniture model parts"):
        refresh_parts(saved)

    assert saved.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.part"))


# --- paths / groups use the extra parts -----------------------------------------

def test_model_paths_include_extra_parts_after_main():
    assert model_paths(405, ["fun_b0_m0405a.mdl"]) == [
        model_path(405),
        f"{GENERAL}/0405/bgparts/fun_b0_m0405a.mdl",
    ]
    assert model_paths(405, ["fun_b0_m0405.mdl"]) == [model_path(405)]  # no duplicate main
    assert model_paths(10000, ["x.mdl"]) == []


def test_hide_files_include_extra_parts():
    files = hide_files([FurnitureModel(405, [(1, "Door")]), FurnitureModel(7, [(2, "Chair")])],
                       "files\\replacement.mdl", {405: ["fun_b0_m0405a.mdl"]})
    assert set(files) == {model_path(405), f"{GENERAL}/0405/bgparts/fun_b0_m0405a.mdl", model_path(7)}
