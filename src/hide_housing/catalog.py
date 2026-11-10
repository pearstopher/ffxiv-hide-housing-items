"""Build the furniture catalog: top-level group -> subcategory -> furniture model.

See docs/furniture-paths.md for how the sheets link together. Key decisions:

- ``HousingFurniture`` is the master list; ~400 furniture items are not in the
  housing catalog (``FurnitureCatalogItemList``).
- Entries are grouped by ``ModelKey`` because hiding a model hides every item
  that uses it (122 models are shared by several items).
- When an item is in the catalog, its catalog subcategory (and that
  subcategory's top-level group) is used, matching where players find it.
  Otherwise it goes under "Other" in its ``HousingItemCategory`` top level.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hide_housing.sheets import read_sheet

# HousingItemCategory values for indoor furniture, in in-game tab order.
TOP_LEVEL_NAMES: dict[int, str] = {
    12: "Furnishings",
    13: "Tables",
    14: "Tabletop",
    15: "Wall-mounted",
    16: "Rugs",
}
OTHER_SUBCATEGORY = "Other"

Rows = Mapping[int, Mapping[str, Any]]


@dataclass
class FurnitureModel:
    model_key: int
    items: list[tuple[int, str]]  # (item id, name), sorted by item id

    @property
    def name(self) -> str:
        """Display name: the name of the earliest (lowest id) item using this model."""
        return self.items[0][1]

    @property
    def item_names(self) -> list[str]:
        return [name for _, name in self.items]


@dataclass
class Subcategory:
    name: str
    sort_order: int
    catalog_id: int | None  # None for the "Other" bucket
    models: list[FurnitureModel] = field(default_factory=list)


@dataclass
class TopLevel:
    id: int
    name: str
    subcategories: list[Subcategory] = field(default_factory=list)

    @property
    def models(self) -> list[FurnitureModel]:
        return [m for sub in self.subcategories for m in sub.models]


@dataclass
class Catalog:
    top_levels: list[TopLevel]
    skipped: list[str] = field(default_factory=list)  # human-readable reasons

    @property
    def models(self) -> list[FurnitureModel]:
        return [m for top in self.top_levels for m in top.models]


def build_catalog(
    furniture: Rows,
    catalog_items: Rows,
    categories: Rows,
    item_names: Mapping[int, str],
) -> Catalog:
    """Combine parsed sheets into a sorted :class:`Catalog`.

    ``furniture`` rows need Item, ModelKey, HousingItemCategory; ``catalog_items``
    rows need Item, Category; ``categories`` rows need Category, Unknown0
    (top level) and Unknown1 (sort order).
    """
    item_to_category = {row["Item"]: row["Category"] for row in catalog_items.values()}
    skipped: list[str] = []

    # model key -> (top level id, catalog category id or None, [(item id, name)])
    grouped: dict[int, tuple[int, int | None, list[tuple[int, str]]]] = {}
    for row_id, row in sorted(furniture.items()):
        item_id, model_key, top_id = row["Item"], row["ModelKey"], row["HousingItemCategory"]
        if item_id == 0 or model_key == 0:
            continue  # unused row
        name = item_names.get(item_id, "").strip()
        if not name:
            skipped.append(f"item {item_id} (model {model_key}): no name")
            continue
        category_id = item_to_category.get(item_id)
        if category_id is not None:
            top_id = categories[category_id]["Unknown0"]
        if top_id not in TOP_LEVEL_NAMES:
            skipped.append(f"{name} (model {model_key}): unknown top level {top_id}")
            continue
        if model_key in grouped:
            _, known_category, items = grouped[model_key]
            items.append((item_id, name))
            if known_category is None and category_id is not None:
                grouped[model_key] = (top_id, category_id, items)
        else:
            grouped[model_key] = (top_id, category_id, [(item_id, name)])

    tops = {tid: TopLevel(tid, tname) for tid, tname in TOP_LEVEL_NAMES.items()}
    subs: dict[tuple[int, int | None], Subcategory] = {}
    for model_key, (top_id, category_id, items) in grouped.items():
        key = (top_id, category_id)
        if key not in subs:
            if category_id is None:
                sub = Subcategory(OTHER_SUBCATEGORY, sort_order=10**6, catalog_id=None)
            else:
                cat = categories[category_id]
                sub = Subcategory(cat["Category"], sort_order=cat["Unknown1"], catalog_id=category_id)
            subs[key] = sub
            tops[top_id].subcategories.append(sub)
        subs[key].models.append(FurnitureModel(model_key, sorted(items)))

    for top in tops.values():
        top.subcategories.sort(key=lambda s: (s.sort_order, s.name))
        for sub in top.subcategories:
            sub.models.sort(key=lambda m: (m.name.casefold(), m.model_key))

    return Catalog([top for top in tops.values() if top.subcategories], skipped)


def load_catalog(sheet_paths: Mapping[str, Path]) -> Catalog:
    """Read the four downloaded sheets (see download.SHEETS) and build the catalog."""
    furniture = read_sheet(
        sheet_paths["HousingFurniture"],
        {"Item": int, "ModelKey": int, "HousingItemCategory": int},
    )
    catalog_items = read_sheet(sheet_paths["FurnitureCatalogItemList"], {"Item": int, "Category": int})
    categories = read_sheet(
        sheet_paths["FurnitureCatalogCategory"],
        {"Category": str, "Unknown0": int, "Unknown1": int},
    )
    # Item.csv has ~50k rows; keep only names of items that are furniture.
    furniture_items = {row["Item"] for row in furniture.values()}
    item_names = {
        item_id: row["Name"]
        for item_id, row in read_sheet(sheet_paths["Item"], {"Name": str}).items()
        if item_id in furniture_items
    }
    return build_catalog(furniture, catalog_items, categories, item_names)
