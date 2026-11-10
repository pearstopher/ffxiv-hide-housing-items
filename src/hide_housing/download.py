"""Download and cache the datamining CSVs this project needs."""

from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/xivapi/ffxiv-datamining/master/csv/en/"
SHEETS = (
    "FurnitureCatalogItemList",
    "FurnitureCatalogCategory",
    "HousingFurniture",
    "Item",
)
DEFAULT_CACHE_DIR = Path(".cache") / "datamining"
TIMEOUT_SECONDS = 60
USER_AGENT = "hide-housing"


class DownloadError(RuntimeError):
    """Raised when a datamining CSV cannot be downloaded."""


def sheet_url(sheet: str) -> str:
    return f"{BASE_URL}{sheet}.csv"


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise DownloadError(f"Could not download {url}: HTTP {exc.code} {exc.reason}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        raise DownloadError(f"Could not download {url}: {reason}") from exc


def download_sheets(
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
    refresh: bool = False,
    sheets: tuple[str, ...] = SHEETS,
) -> dict[str, Path]:
    """Return {sheet name: local CSV path}, downloading any missing sheets.

    Cached files are reused unless ``refresh`` is true. Files are written to a
    temporary name first so a failed download never leaves a partial CSV behind.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for sheet in sheets:
        path = cache_dir / f"{sheet}.csv"
        if refresh or not path.is_file():
            data = _fetch(sheet_url(sheet))
            tmp = path.with_suffix(".csv.part")
            tmp.write_bytes(data)
            tmp.replace(path)
        paths[sheet] = path
    return paths
