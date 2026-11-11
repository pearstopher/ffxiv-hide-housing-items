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
from hide_housing.catchall import catch_all_groups, catch_all_option_specs, effects_groups
from hide_housing.download import DEFAULT_CACHE_DIR, DownloadError, download_sheets
from hide_housing.groups import all_groups
from hide_housing.meta import ModInfo, build_meta, write_meta
from hide_housing.package import DEFAULT_DIST_DIR, PackageError, package_mod
from hide_housing.parts import Parts, load_indoor_vfx, load_parts, refresh_parts
from hide_housing.sheets import SheetError

log = logging.getLogger("hide_housing")


@dataclass
class BuildResult:
    output: Path
    catalog: Catalog
    group_count: int
    option_count: int
    parts: Parts
    parts_status: str
    indoor_vfx_count: int = 0

    def summary(self) -> str:
        cat = self.catalog
        subcategories = sum(len(top.subcategories) for top in cat.top_levels)
        models = cat.models
        items = sum(len(m.items) for m in models)
        multi = [m for m in models if self.parts.get(m.model_key)]
        extra_files = sum(len(self.parts[m.model_key]) for m in multi)
        lines = [
            f"Tabs:          {len(cat.top_levels)}",
            f"Categories:    {subcategories}",
            f"Models:        {len(models)}",
            f"Items:         {items}",
            f"Groups:        {self.group_count} ({self.option_count} options)",
            f"Multi-part:    {len(multi)} models (+{extra_files} extra part files)",
            f"Indoor VFX:    {self.indoor_vfx_count} effects",
            f"Parts list:    {self.parts_status}",
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
    refresh_parts_list: bool = False,
) -> BuildResult:
    """Download -> parse -> catalog -> groups -> meta.json -> .pmp.

    Extra model parts come from the saved parts list (hide_housing.parts); it is
    only downloaded again when ``refresh_parts_list`` is true.
    """
    if refresh_parts_list:
        log.info("Refreshing the saved model parts list")
        parts, changed = refresh_parts()
        parts_status = "refreshed, saved file updated" if changed else "refreshed, no changes"
    else:
        parts = load_parts()
        parts_status = "saved file"
    indoor_vfx = load_indoor_vfx()
    log.info("Fetching datamining sheets into %s%s", cache_dir, " (refresh)" if refresh else "")
    sheet_paths = download_sheets(cache_dir, refresh=refresh)
    catalog = load_catalog(sheet_paths)
    with tempfile.TemporaryDirectory(prefix="hide_housing_build_") as tmp:
        build_dir = Path(tmp)
        replacement_path = bundle_replacement(build_dir, replacement)
        specs = catch_all_option_specs(
            sheet_paths.get("GardeningSeed"), sheet_paths.get("HousingFurniture"), parts
        )
        catch_all = catch_all_groups(specs, replacement_path) + effects_groups(indoor_vfx)
        groups = all_groups(catalog, replacement_path, parts, catch_all)
        write_meta(build_dir, build_meta(info, groups))
        output = package_mod(build_dir, out_dir)
    return BuildResult(
        output=output.resolve(),
        catalog=catalog,
        group_count=len(groups),
        option_count=sum(len(g["Options"]) for g in groups),
        parts=parts,
        parts_status=parts_status,
        indoor_vfx_count=len(indoor_vfx),
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
    b.add_argument("--refresh-parts", action="store_true",
                   help="re-download the game path list and update the saved model parts and indoor VFX lists if they changed")
    b.add_argument("-v", "--verbose", action="store_true", help="show progress and warnings")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = make_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    try:
        result = build(args.out, args.cache_dir, args.refresh, args.replacement,
                       refresh_parts_list=args.refresh_parts)
    except (DownloadError, SheetError, PackageError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(result.summary())
    return 0
