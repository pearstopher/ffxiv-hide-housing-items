"""Check the data chain documented in docs/furniture-paths.md against real fixture rows."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def read(name):
    with open(FIXTURES / f"{name}.csv", encoding="utf-8", newline="") as f:
        return {row["#"]: row for row in csv.DictReader(f)}


def model_path(model_key):
    key = f"{int(model_key):04d}"
    return f"bgcommon/hou/indoor/general/{key}/bgparts/fun_b0_m{key}.mdl"


def test_model_key_633_is_the_stage_panel_in_the_example():
    furniture = read("HousingFurniture")
    items = read("Item")
    row = next(r for r in furniture.values() if r["ModelKey"] == "633")
    assert items[row["Item"]]["Name"] == "Stage Panel"

    example = json.loads((ROOT / "example" / "meta.json").read_text(encoding="utf-8"))
    assert model_path(row["ModelKey"]) in example["DefaultData"]["Files"]


def test_catalog_category_links_to_top_level_group():
    furniture = read("HousingFurniture")
    catalog = {r["Item"]: r for r in read("FurnitureCatalogItemList").values()}
    categories = read("FurnitureCatalogCategory")
    stage = next(r for r in furniture.values() if r["ModelKey"] == "633")
    category = categories[catalog[stage["Item"]]["Category"]]
    assert category["Category"] == "Walls/Pillars/Partitions"
    assert category["Unknown0"] == stage["HousingItemCategory"] == "12"


def test_shared_model_key_and_items_missing_from_catalog():
    furniture = read("HousingFurniture")
    catalog_items = {r["Item"] for r in read("FurnitureCatalogItemList").values()}
    sheep = [r for r in furniture.values() if r["ModelKey"] == "290"]
    assert len(sheep) == 2
    assert not any(r["Item"] in catalog_items for r in sheep)


def test_unused_rows_have_zero_item_and_model_key():
    assert read("HousingFurniture")["196608"]["Item"] == "0"


def test_model_key_padding():
    assert model_path(7).endswith("/0007/bgparts/fun_b0_m0007.mdl")
    assert model_path(1637).endswith("/1637/bgparts/fun_b0_m1637.mdl")
