"""The replacement model that hidden furniture is swapped for.

The default is a simple stand-in model (a copy of ``example/files/table_mat.mdl``)
until #15 provides an invisible one. Pass ``source`` to use a different file.
"""

from __future__ import annotations

import shutil
from importlib import resources
from pathlib import Path

FILES_DIR = "files"
REPLACEMENT_NAME = "replacement.mdl"


def default_replacement() -> Path:
    """Path of the replacement model shipped with the package."""
    return Path(str(resources.files("hide_housing") / "assets" / REPLACEMENT_NAME))


def bundle_replacement(build_dir: Path | str, source: Path | str | None = None) -> str:
    r"""Copy the replacement model into ``<build_dir>/files/``.

    Returns the mod-relative path to use as the value in Penumbra ``Files`` maps,
    written with a Windows backslash as Penumbra does (``files\replacement.mdl``).
    """
    source = Path(source) if source is not None else default_replacement()
    if not source.is_file():
        raise FileNotFoundError(f"Replacement model not found: {source}")
    if source.suffix.lower() != ".mdl":
        raise ValueError(f"Replacement must be a .mdl file, got {source.name}")

    files_dir = Path(build_dir) / FILES_DIR
    files_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, files_dir / REPLACEMENT_NAME)
    return f"{FILES_DIR}\\{REPLACEMENT_NAME}"
