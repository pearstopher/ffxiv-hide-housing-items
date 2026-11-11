"""Extra model parts of multi-part furniture (doors, canopy beds, partitions...).

Some furniture has more ``.mdl`` files next to its main ``fun_b0_m{NNNN}.mdl``,
e.g. ``fun_b0_m0405a.mdl`` (a door leaf). They are found in the ResLogger2 path
list (see docs/furniture-paths.md, "Multi-part furniture"). That list is ~8 MB,
so it is **not** read on every build: the extra part names are extracted once
and saved to ``data/model_parts.json``, which builds read. ``refresh_parts()``
downloads the list again and rewrites the saved file only if the parts changed.
"""

from __future__ import annotations

import gzip
import json
import re
from collections.abc import Iterable, Mapping
from importlib import resources
from pathlib import Path

from hide_housing.download import DownloadError, _fetch

PATH_LIST_URL = "https://rl2.perchbird.dev/download/export/CurrentPathList.gz"
_BGPARTS_MDL = re.compile(r"^bgcommon/hou/indoor/general/(\d{4})/bgparts/([^/]+\.mdl)$")

Parts = dict[int, list[str]]


def default_parts_file() -> Path:
    """The saved parts list shipped with the package."""
    return Path(str(resources.files("hide_housing") / "data" / "model_parts.json"))


def extract_parts(lines: Iterable[str]) -> Parts:
    """``{model key: [extra .mdl names]}`` from game paths, one per line.

    Only ``.mdl`` files in ``indoor/general/{NNNN}/bgparts/`` are considered, and
    the main ``fun_b0_m{NNNN}.mdl`` is left out (it is always replaced anyway).
    Keys without extra parts are omitted. Names are sorted.
    """
    found: dict[int, set[str]] = {}
    for line in lines:
        match = _BGPARTS_MDL.match(line.strip())
        if not match:
            continue
        key, name = int(match.group(1)), match.group(2)
        if name != f"fun_b0_m{key:04d}.mdl":
            found.setdefault(key, set()).add(name)
    return {key: sorted(names) for key, names in sorted(found.items())}


def _to_json(parts: Mapping[int, list[str]]) -> str:
    data = {
        "source": PATH_LIST_URL,
        "parts": {f"{key:04d}": names for key, names in sorted(parts.items())},
    }
    return json.dumps(data, indent=2) + "\n"


def load_parts(path: Path | str | None = None) -> Parts:
    """Read a saved parts list (default: the one shipped with the package)."""
    path = Path(path) if path is not None else default_parts_file()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {int(key): list(names) for key, names in data["parts"].items()}
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Saved parts list not found: {path}. Run the build with --refresh-parts to create it."
        ) from None
    except (json.JSONDecodeError, KeyError, ValueError, TypeError, AttributeError) as exc:
        raise ValueError(f"Saved parts list {path} is invalid: {exc}") from exc


# --- Indoor housing effects (VFX) ------------------------------------------------
# Every .avfx under bgcommon/hou/common/vfx_hou_ind1/ in the path list. Saved next
# to the parts list and refreshed by the same refresh_parts() download (#49).
INDOOR_VFX_PREFIX = "bgcommon/hou/common/vfx_hou_ind1/"
INDOOR_VFX_FILENAME = "indoor_vfx.json"


def vfx_file_for(parts_file: Path) -> Path:
    """The saved indoor VFX list lives next to the saved parts list."""
    return Path(parts_file).with_name(INDOOR_VFX_FILENAME)


def extract_indoor_vfx(lines: Iterable[str]) -> list[str]:
    """Sorted, unique ``.avfx`` game paths under ``vfx_hou_ind1``."""
    return sorted({
        line.strip() for line in lines
        if line.startswith(INDOOR_VFX_PREFIX) and line.strip().endswith(".avfx")
    })


def load_indoor_vfx(path: Path | str | None = None) -> list[str]:
    """Read the saved indoor VFX list (default: the one shipped with the package)."""
    path = Path(path) if path is not None else vfx_file_for(default_parts_file())
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        vfx = data["vfx"]
        if not isinstance(vfx, list) or not all(isinstance(p, str) for p in vfx):
            raise TypeError("'vfx' must be a list of paths")
        return list(vfx)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Saved indoor VFX list not found: {path}. Run the build with --refresh-parts to create it."
        ) from None
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"Saved indoor VFX list {path} is invalid: {exc}") from exc


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.part")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def refresh_parts(path: Path | str | None = None) -> tuple[Parts, bool]:
    """Download the path list once and update the saved lists that changed.

    Updates the multi-part list (``path``) and the indoor VFX list next to it.
    Returns ``(parts, changed)``; ``changed`` is true if either file was
    rewritten. Unchanged lists are left untouched. If the download has no
    indoor VFX, the saved VFX list is kept as it is.
    """
    path = Path(path) if path is not None else default_parts_file()
    raw = _fetch(PATH_LIST_URL)
    try:
        text = gzip.decompress(raw).decode("utf-8", errors="replace")
    except (OSError, EOFError) as exc:
        raise DownloadError(f"Could not read {PATH_LIST_URL}: {exc}") from exc
    lines = text.splitlines()
    parts = extract_parts(lines)
    if not parts:
        raise DownloadError(f"{PATH_LIST_URL} contained no furniture model parts; not saving")

    try:
        parts_changed = load_parts(path) != parts
    except (FileNotFoundError, ValueError):
        parts_changed = True
    if parts_changed:
        _write(path, _to_json(parts))

    vfx = extract_indoor_vfx(lines)
    vfx_path = vfx_file_for(path)
    vfx_changed = False
    if vfx:
        try:
            vfx_changed = load_indoor_vfx(vfx_path) != vfx
        except (FileNotFoundError, ValueError):
            vfx_changed = True
        if vfx_changed:
            _write(vfx_path, json.dumps({"source": PATH_LIST_URL, "vfx": vfx}, indent=2) + "\n")
    return parts, parts_changed or vfx_changed
