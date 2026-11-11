import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from hide_housing import cli, download

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def cache(tmp_path):
    """A cache dir pre-filled with the fixture CSVs, so nothing is downloaded."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    for sheet in download.SHEETS:
        shutil.copy(FIXTURES / f"{sheet}.csv", cache_dir / f"{sheet}.csv")
    return cache_dir


@pytest.fixture
def no_network(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(download.urllib.request, "urlopen", fail)


def test_build_end_to_end_offline(tmp_path, cache, no_network, capsys):
    out = tmp_path / "dist"
    assert cli.main(["build", "--cache-dir", str(cache), "--out", str(out)]) == 0

    pmp = out / "hide-housing-furniture-0.1.0.pmp"
    with zipfile.ZipFile(pmp) as archive:
        assert set(archive.namelist()) == {"meta.json", "files/replacement.mdl"}
        meta = json.loads(archive.read("meta.json"))
    assert meta["Author"] == "Ane Mora"
    assert [g["Name"] for g in meta["Groups"]][:2] == [
        "Furnishings: hide whole categories",
        "Tables: hide whole categories",
    ]

    summary = capsys.readouterr().out
    for line in ["Tabs:          3", "Categories:    3", "Models:        3", "Items:         4",
                 "Groups:        7 (7 options)", "Skipped:       0", "Parts list:    saved file",
                 f"Output:        {pmp.resolve()}"]:
        assert line in summary


def test_skipped_items_are_listed(tmp_path, cache, no_network, capsys):
    items = cache / "Item.csv"
    items.write_text(items.read_text(encoding="utf-8").replace("Stage Panel", ""), encoding="utf-8")
    assert cli.main(["build", "--cache-dir", str(cache), "--out", str(tmp_path / "dist")]) == 0
    summary = capsys.readouterr().out
    assert "Skipped:       1" in summary
    assert "  - item 21839 (model 633): no name" in summary


def test_refresh_downloads(tmp_path, cache, monkeypatch, capsys):
    fetched = []

    def fake_fetch(url):
        fetched.append(url)
        return (FIXTURES / url.rsplit("/", 1)[1]).read_bytes()

    monkeypatch.setattr(download, "_fetch", fake_fetch)
    assert cli.main(["build", "--refresh", "--cache-dir", str(cache), "--out", str(tmp_path / "d")]) == 0
    assert len(fetched) == len(download.SHEETS)


def test_custom_replacement(tmp_path, cache, no_network, capsys):
    custom = tmp_path / "invisible.mdl"
    custom.write_bytes(b"\x00invisible")
    out = tmp_path / "dist"
    assert cli.main(["build", "--cache-dir", str(cache), "--out", str(out),
                     "--replacement", str(custom)]) == 0
    with zipfile.ZipFile(out / "hide-housing-furniture-0.1.0.pmp") as archive:
        assert archive.read("files/replacement.mdl") == b"\x00invisible"


def test_errors_are_reported_without_traceback(tmp_path, cache, no_network, capsys):
    (cache / "HousingFurniture.csv").write_text("not,a,sheet\n", encoding="utf-8")
    assert cli.main(["build", "--cache-dir", str(cache), "--out", str(tmp_path / "d")]) == 1
    err = capsys.readouterr().err
    assert err.startswith("error: HousingFurniture.csv: first column")


def test_build_command_required(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main([])
    assert exc.value.code == 2


def test_python_dash_m_entry_point():
    result = subprocess.run(
        [sys.executable, "-m", "hide_housing", "--version"], capture_output=True, text=True, check=True
    )
    assert "0.1.0" in result.stdout


def test_multi_part_models_get_every_part_from_saved_list(tmp_path, cache, no_network, capsys, monkeypatch):
    saved = tmp_path / "model_parts.json"
    saved.write_text(json.dumps({"parts": {"0633": ["fun_b0_m0633a.mdl", "fun_b0_m0633b.mdl"]}}),
                     encoding="utf-8")
    monkeypatch.setattr("hide_housing.parts.default_parts_file", lambda: saved)
    out = tmp_path / "dist"
    assert cli.main(["build", "--cache-dir", str(cache), "--out", str(out)]) == 0

    with zipfile.ZipFile(out / "hide-housing-furniture-0.1.0.pmp") as archive:
        meta = json.loads(archive.read("meta.json"))
    stage = next(o for g in meta["Groups"] for o in g["Options"] if o["Name"] == "Stage Panel")
    folder = "bgcommon/hou/indoor/general/0633/bgparts"
    assert sorted(stage["Files"]) == [f"{folder}/fun_b0_m0633.mdl", f"{folder}/fun_b0_m0633a.mdl",
                                      f"{folder}/fun_b0_m0633b.mdl"]
    assert "Multi-part:    1 models (+2 extra part files)" in capsys.readouterr().out


def test_refresh_parts_flag_updates_saved_file(tmp_path, cache, capsys, monkeypatch):
    import gzip
    from hide_housing import parts
    saved = tmp_path / "model_parts.json"
    monkeypatch.setattr(parts, "default_parts_file", lambda: saved)
    listing = "bgcommon/hou/indoor/general/0633/bgparts/fun_b0_m0633a.mdl\n"
    monkeypatch.setattr(parts, "_fetch", lambda url: gzip.compress(listing.encode()))

    args = ["build", "--refresh-parts", "--cache-dir", str(cache), "--out", str(tmp_path / "d")]
    assert cli.main(args) == 0
    assert "Parts list:    refreshed, saved file updated" in capsys.readouterr().out
    assert json.loads(saved.read_text())["parts"] == {"0633": ["fun_b0_m0633a.mdl"]}

    assert cli.main(args) == 0
    assert "Parts list:    refreshed, no changes" in capsys.readouterr().out
