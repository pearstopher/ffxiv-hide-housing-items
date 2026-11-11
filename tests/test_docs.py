"""Keep the user docs in sync with the code."""

import re
from pathlib import Path

from hide_housing.cli import make_parser

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def build_parser_flags():
    parser = make_parser()
    build = parser._subparsers._group_actions[0].choices["build"]
    return {flag for action in build._actions for flag in action.option_strings}


def test_readme_documents_every_build_flag():
    flags = build_parser_flags() - {"-h", "--help"}
    for flag in flags:
        assert f"`{flag}" in README or f"`{flag}`" in README, f"{flag} missing from README"


def test_readme_flags_exist():
    documented = set(re.findall(r"`(--?[a-z][a-z-]*)", README))
    assert documented <= build_parser_flags()


def test_readme_mentions_build_command_and_output_name():
    assert "python -m hide_housing build" in README
    assert "dist/hide-housing-furniture-<version>.pmp" in README


def test_doc_links_resolve():
    for link in re.findall(r"\]\((docs/[^)#]+)\)", README):
        assert (ROOT / link).is_file(), link


def test_testing_checklist_covers_required_steps():
    checklist = (ROOT / "docs" / "testing.md").read_text(encoding="utf-8")
    for step in ["Hide one category", "Hide one item", "Everything off again"]:
        assert step in checklist


PRESETS = {"Hide Everything": "presets/hide-everything.txt", "Rainbow Cafe": "presets/rainbow-cafe.txt"}


def test_readme_lists_every_preset_file():
    for name, path in PRESETS.items():
        assert (ROOT / path).is_file(), path
        assert f"| {name} | [`{path}`]({path}) |" in README


def test_preset_files_are_valid_penumbra_presets():
    import base64
    import gzip
    import json

    for name, path in PRESETS.items():
        text = (ROOT / path).read_text(encoding="utf-8").strip()
        assert text, f"{name} preset is empty"
        data = gzip.decompress(base64.b64decode(text))
        assert data[0] == 1, "Penumbra preset format version byte"
        preset = json.loads(data[1:])
        assert preset["Settings"], name
        for group in preset["Settings"]:
            assert group["Identifier"] and group["Name"]
            for option in group.get("Options", []):
                assert option["State"] in ("Enabled", "Disabled")


def test_unlicense_is_set_up():
    licence = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert licence.startswith("This is free and unencumbered software released into the public domain.")
    assert "<https://unlicense.org>" in licence
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'license = "Unlicense"' in pyproject
    assert "[The Unlicense](LICENSE)" in README
