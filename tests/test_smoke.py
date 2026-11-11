import tomllib
from pathlib import Path

import hide_housing

PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def test_package_version_matches_pyproject():
    with PYPROJECT.open("rb") as f:
        assert hide_housing.__version__ == tomllib.load(f)["project"]["version"]


def test_version_is_semver():
    major, minor, patch = hide_housing.__version__.split(".")
    assert all(part.isdigit() for part in (major, minor, patch))
