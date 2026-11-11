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


def refresh_parts(path: Path | str | None = None) -> tuple[Parts, bool]:
    """Download the path list, extract the parts and save them if they changed.

    Returns ``(parts, changed)``. The file is only rewritten when the extracted
    parts differ from what is saved, so an unchanged refresh leaves it untouched.
    """
    path = Path(path) if path is not None else default_parts_file()
    raw = _fetch(PATH_LIST_URL)
    try:
        text = gzip.decompress(raw).decode("utf-8", errors="replace")
    except (OSError, EOFError) as exc:
        raise DownloadError(f"Could not read {PATH_LIST_URL}: {exc}") from exc
    parts = extract_parts(text.splitlines())
    if not parts:
        raise DownloadError(f"{PATH_LIST_URL} contained no furniture model parts; not saving")

    try:
        changed = load_parts(path) != parts
    except (FileNotFoundError, ValueError):
        changed = True
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.part")
        tmp.write_text(_to_json(parts), encoding="utf-8", newline="\n")
        tmp.replace(path)
    return parts, changed
