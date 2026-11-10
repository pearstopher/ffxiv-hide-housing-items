"""Read xivapi datamining CSV sheets into records keyed by row ID.

Format: one header row whose first column is ``#`` (the row ID), then one
record per row. Fields may be quoted and contain commas or newlines.
"""

from __future__ import annotations

import csv
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

ID_COLUMN = "#"


class SheetError(ValueError):
    """Raised when a sheet is missing expected columns or has bad values."""


def to_bool(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"expected True or False, got {value!r}")


Converter = Callable[[str], Any]


def read_sheet(
    path: Path | str,
    columns: Mapping[str, Converter] | None = None,
) -> dict[int, dict[str, Any]]:
    """Return ``{row id: {column: value}}`` for a datamining CSV.

    ``columns`` maps the column names to keep to a converter such as ``int``,
    ``str`` or ``to_bool``. Other columns are dropped, which keeps the ~20 MB
    ``Item.csv`` small in memory. With ``columns=None`` every column is kept
    as a string.
    """
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            raise SheetError(f"{path.name}: file is empty") from None
        if not header or header[0] != ID_COLUMN:
            raise SheetError(f"{path.name}: first column must be {ID_COLUMN!r}")

        wanted = columns if columns is not None else {name: str for name in header[1:]}
        missing = [name for name in wanted if name not in header]
        if missing:
            raise SheetError(f"{path.name}: missing column(s) {', '.join(missing)}")
        indexes = {name: header.index(name) for name in wanted}

        records: dict[int, dict[str, Any]] = {}
        for line_no, row in enumerate(reader, start=2):
            if not row:
                continue
            try:
                row_id = int(row[0])
                records[row_id] = {
                    name: convert(row[indexes[name]]) for name, convert in wanted.items()
                }
            except (ValueError, IndexError) as exc:
                raise SheetError(f"{path.name}: bad row {line_no}: {exc}") from exc
        return records
