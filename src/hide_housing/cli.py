"""Command line: ``python -m hide_housing build``."""

from __future__ import annotations

import argparse
import logging
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from hide_housing import __version__
from hide_housing.assets import bundle_replacement
from hide_housing.catalog import Catalog, load_catalog
from hide_housing.download import DEFAULT_CACHE_DIR, DownloadError, download_sheets
from hide_housing.groups import all_groups
from hide_housing.meta import ModInfo, build_meta, write_meta
from hide_housing.package import DEFAULT_DIST_DIR, PackageError, package_mod
from hide_housing.sheets import SheetError

log = logging.getLogger("hide_housing")


@dataclass
class BuildResult:
    output: Path
    catalog: Catalog
    group_count: int
    option_count: int

    def summary(self) -> str:
        cat = self.catalog
        subcategories = sum(len(top.subcategories) for top in cat.top_levels)
        models = cat.models
        items = sum(len(m.items) for m in models)
        lines = [
            f"Tabs:          {len(cat.top_levels)}",
            f"Categories:    {subcategories}",
            f"Models:        {len(models)}",
            f"Items:         {items}",
            f"Groups:        {self.group_count} ({self.option_count} options)",
            f"Skipped:       {len(cat.skipped)}",
        ]
        lines += [f"  - {reason}" for reason in cat.skipped]
        lines.append(f"Output:        {self.output}")
        return "\n".join(lines)


def build(
    out_dir: Path | str = DEFAULT_DIST_DIR,
    cache_dir: Path | str = DEFAULT_CACHE_DIR,
    refresh: bool = False,
    replacement: Path | str | None = None,
    info: ModInfo = ModInfo(),
) -> BuildResult:
    """Download -> parse -> catalog -> groups -> meta.json -> .pmp."""
    log.info("Fetching datamining sheets into %s%s", cache_dir, " (refresh)" if refresh else "")
    sheet_paths = download_sheets(cache_dir, refresh=refresh)
    catalog = load_catalog(sheet_paths)
    with tempfile.TemporaryDirectory(prefix="hide_housing_build_") as tmp:
        build_dir = Path(tmp)
        replacement_path = bundle_replacement(build_dir, replacement)
        groups = all_groups(catalog, replacement_path)
        write_meta(build_dir, build_meta(info, groups))
        output = package_mod(build_dir, out_dir)
    return BuildResult(
        output=output.resolve(),
        catalog=catalog,
        group_count=len(groups),
        option_count=sum(len(g["Options"]) for g in groups),
    )


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m hide_housing",
        description="Generate a Penumbra mod that hides FFXIV indoor housing furniture.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    b = commands.add_parser("build", help="build the .pmp from the latest datamining")
    b.add_argument("--refresh", action="store_true", help="re-download the datamining CSVs")
    b.add_argument("--out", type=Path, default=DEFAULT_DIST_DIR, metavar="DIR",
                   help=f"output directory for the .pmp (default: {DEFAULT_DIST_DIR})")
    b.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, metavar="DIR",
                   help=f"where downloaded CSVs are kept (default: {DEFAULT_CACHE_DIR})")
    b.add_argument("--replacement", type=Path, metavar="MDL",
                   help="use this .mdl instead of the bundled replacement model")
    b.add_argument("-v", "--verbose", action="store_true", help="show progress and warnings")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    try:
        result = build(args.out, args.cache_dir, args.refresh, args.replacement)
    except (DownloadError, SheetError, PackageError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(result.summary())
    return 0
