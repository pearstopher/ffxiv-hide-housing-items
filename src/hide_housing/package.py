"""Package a build directory into a Penumbra ``.pmp`` (a zip with another extension)."""

from __future__ import annotations

import json
import re
import zipfile
from collections.abc import Iterator, Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from hide_housing.meta import META_FILENAME

DEFAULT_DIST_DIR = Path("dist")
# Fixed timestamp so rebuilding identical content gives an identical archive.
ZIP_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


class PackageError(ValueError):
    """Raised when a build directory is not a valid mod."""


def pmp_filename(name: str, version: str) -> str:
    """``"Hide Housing Furniture", "1.0.0"`` -> ``"hide-housing-furniture-1.0.0.pmp"``."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "mod"
    safe_version = re.sub(r"[^A-Za-z0-9._-]+", "-", version).strip("-") or "0"
    return f"{slug}-{safe_version}.pmp"


def iter_containers(meta: Mapping[str, Any]) -> Iterator[Mapping[str, Any]]:
    """``DefaultData`` and every option of every group."""
    if meta.get("DefaultData"):
        yield meta["DefaultData"]
    for group in meta.get("Groups") or []:
        yield from group.get("Options") or []


def referenced_files(meta: Mapping[str, Any]) -> set[str]:
    """Mod-relative paths (POSIX form) of every file redirected to in ``meta``."""
    return {
        PureWindowsPath(mod_path).as_posix()
        for container in iter_containers(meta)
        for mod_path in (container.get("Files") or {}).values()
    }


def check_build(build_dir: Path) -> dict[str, Any]:
    """Validate the build dir; return the parsed meta.json."""
    meta_path = build_dir / META_FILENAME
    if not meta_path.is_file():
        raise PackageError(f"{meta_path} not found")
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PackageError(f"{meta_path} is not valid JSON: {exc}") from exc
    missing = sorted(p for p in referenced_files(meta) if not (build_dir / p).is_file())
    if missing:
        raise PackageError(f"meta.json references missing file(s): {', '.join(missing)}")
    return meta


def package_mod(build_dir: Path | str, dist_dir: Path | str = DEFAULT_DIST_DIR) -> Path:
    """Zip ``build_dir`` into ``<dist_dir>/<name>-<version>.pmp`` and return its path.

    The archive has ``meta.json`` at its root, entries in sorted order with
    forward-slash names and fixed timestamps, so identical builds produce
    identical files.
    """
    build_dir = Path(build_dir)
    meta = check_build(build_dir)
    dist_dir = Path(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)
    out = dist_dir / pmp_filename(meta.get("Name", ""), str(meta.get("Version") or "0"))

    files = sorted(p for p in build_dir.rglob("*") if p.is_file())
    tmp = out.with_suffix(".pmp.part")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            arcname = PurePosixPath(*path.relative_to(build_dir).parts).as_posix()
            info = zipfile.ZipInfo(arcname, date_time=ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    tmp.replace(out)
    return out
