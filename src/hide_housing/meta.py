"""Build and write the Penumbra ``meta.json`` (FileVersion 4).

See docs/penumbra-format.md. Everything lives in one ``meta.json``: mod info, an
empty ``DefaultData`` (nothing is hidden unless the player turns it on) and the
option groups. IDs are deterministic uuid5 values so rebuilding the same data
produces an identical file.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hide_housing import __version__, penumbra

# Fixed namespace for every ID this project generates. Never change it: doing so
# changes every group/option ID and resets players' saved settings.
ID_NAMESPACE = uuid.UUID("5d7f3c1e-8a0b-4f2e-9c6d-2b1a7e4f0c93")

META_FILENAME = "meta.json"


def stable_id(*parts: str) -> str:
    """Deterministic UUID for a group/option/mod, derived from its name parts."""
    return str(uuid.uuid5(ID_NAMESPACE, "\x1f".join(parts)))


@dataclass(frozen=True)
class ModInfo:
    name: str = "Hide Housing Furniture"
    author: str | None = None
    description: str = (
        "Hide any indoor housing furniture, by whole category or item by item. "
        "Nothing is hidden until you enable options."
    )
    version: str = __version__
    website: str | None = "https://github.com/pearstopher/ffxiv-hide-housing-items"


def option(group_name: str, name: str, files: Mapping[str, str], description: str = "") -> dict[str, Any]:
    """A Multi group option redirecting ``files`` (game path -> mod file path)."""
    return {
        "Id": stable_id("option", group_name, name),
        "Name": name,
        "Description": description,
        "Priority": 0,
        "Files": dict(files),
        "FileSwaps": {},
        "Manipulations": [],
    }


def multi_group(
    name: str,
    options: Sequence[dict[str, Any]],
    priority: int = 0,
    description: str = "",
) -> dict[str, Any]:
    """A Multi group with every option off by default."""
    if len(options) > penumbra.MAX_MULTI_OPTIONS:
        raise ValueError(
            f"Group {name!r} has {len(options)} options; Penumbra allows {penumbra.MAX_MULTI_OPTIONS}"
        )
    return {
        "Version": 0,
        "Id": stable_id("group", name),
        "Name": name,
        "Description": description,
        "Priority": priority,
        "Type": "Multi",
        "DefaultSettings": penumbra.ALL_OPTIONS_OFF,
        "Options": list(options),
    }


def build_meta(info: ModInfo, groups: Sequence[dict[str, Any]] = ()) -> dict[str, Any]:
    """The full meta.json content. ``DefaultData`` is always empty."""
    if not info.name.strip():
        raise ValueError("Mod name must not be empty")
    ids = [g["Id"] for g in groups] + [o["Id"] for g in groups for o in g["Options"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate group/option IDs; group names and option names within a group must be unique")
    return {
        "FileVersion": penumbra.FILE_VERSION,
        "Identifier": stable_id("mod", info.name),
        "Name": info.name,
        "Author": info.author,
        "Description": info.description,
        "Version": info.version,
        "Website": info.website,
        "ModTags": [],
        "DefaultData": {"Files": {}, "FileSwaps": {}, "Manipulations": []},
        "Groups": list(groups),
    }


def write_meta(build_dir: Path | str, meta: Mapping[str, Any]) -> Path:
    """Write ``meta.json`` into ``build_dir`` (UTF-8, 2-space indent, stable output)."""
    path = Path(build_dir) / META_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(meta, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path
