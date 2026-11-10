from pathlib import Path

from hide_housing.catalog import OTHER_SUBCATEGORY, build_catalog, load_catalog

FIXTURES = Path(__file__).resolve().parent / "fixtures"
SHEETS = ("HousingFurniture", "FurnitureCatalogItemList", "FurnitureCatalogCategory", "Item")


def fixture_catalog():
    return load_catalog({name: FIXTURES / f"{name}.csv" for name in SHEETS})


def find(catalog, top_name):
    return next(t for t in catalog.top_levels if t.name == top_name)


# --- fixtures (real data) ---------------------------------------------------

def test_fixture_structure():
    catalog = fixture_catalog()
    assert [t.name for t in catalog.top_levels] == ["Furnishings", "Tables", "Tabletop"]
    assert catalog.skipped == []

    furnishings = find(catalog, "Furnishings")
    assert [s.name for s in furnishings.subcategories] == ["Walls/Pillars/Partitions"]
    assert [(m.model_key, m.name) for m in furnishings.models] == [(633, "Stage Panel")]

    tables = find(catalog, "Tables")
    assert [(s.name, [m.name for m in s.models]) for s in tables.subcategories] == [
        ("Tables", ["Riviera Round Table"])
    ]


def test_shared_model_not_in_catalog_goes_to_other():
    tabletop = find(fixture_catalog(), "Tabletop")
    (other,) = tabletop.subcategories
    assert other.name == OTHER_SUBCATEGORY and other.catalog_id is None
    (sheep,) = other.models
    assert sheep.model_key == 290
    assert sheep.name == "Sheep Dolls"
    assert sheep.item_names == ["Sheep Dolls", "Jumbo Sheep Dolls"]


def test_unused_rows_are_dropped():
    assert {m.model_key for m in fixture_catalog().models} == {1, 290, 633}


# --- synthetic edge cases --------------------------------------------------

CATEGORIES = {
    0: {"Category": "Tables", "Unknown0": 13, "Unknown1": 1},
    1: {"Category": "Shelves/Chests", "Unknown0": 12, "Unknown1": 2},
    4: {"Category": "Chairs/Sofas", "Unknown0": 12, "Unknown1": 1},
}


def furniture(*rows):
    return {i: {"Item": item, "ModelKey": key, "HousingItemCategory": top}
            for i, (item, key, top) in enumerate(rows)}


def catalog_items(**item_to_category):
    return {i: {"Item": int(item[1:]), "Category": cat}
            for i, (item, cat) in enumerate(item_to_category.items())}


def test_blank_names_are_skipped_and_reported():
    catalog = build_catalog(furniture((10, 5, 12), (11, 6, 12)), {}, CATEGORIES, {10: "Chair", 11: " "})
    assert [m.model_key for m in catalog.models] == [5]
    assert catalog.skipped == ["item 11 (model 6): no name"]


def test_unknown_top_level_is_skipped():
    catalog = build_catalog(furniture((10, 5, 99)), {}, CATEGORIES, {10: "Mystery"})
    assert catalog.models == []
    assert "unknown top level 99" in catalog.skipped[0]


def test_catalog_category_decides_top_level():
    # Lattice-windowed Cabinet: HousingItemCategory says Tables, catalog says Furnishings.
    catalog = build_catalog(
        furniture((48116, 1466, 13)), catalog_items(i48116=1), CATEGORIES, {48116: "Cabinet"}
    )
    (top,) = catalog.top_levels
    assert top.name == "Furnishings"
    assert top.subcategories[0].name == "Shelves/Chests"


def test_subcategories_sorted_by_game_order_with_other_last_and_models_by_name():
    catalog = build_catalog(
        furniture((1, 1, 12), (2, 2, 12), (3, 3, 12), (4, 4, 12)),
        catalog_items(i1=1, i2=4, i3=4),
        CATEGORIES,
        {1: "Bookshelf", 2: "stool", 3: "Armchair", 4: "Odd Thing"},
    )
    (top,) = catalog.top_levels
    assert [(s.name, [m.name for m in s.models]) for s in top.subcategories] == [
        ("Chairs/Sofas", ["Armchair", "stool"]),
        ("Shelves/Chests", ["Bookshelf"]),
        (OTHER_SUBCATEGORY, ["Odd Thing"]),
    ]


def test_shared_model_takes_category_from_any_catalogued_item():
    catalog = build_catalog(
        furniture((5, 7, 12), (9, 7, 12)), catalog_items(i9=4), CATEGORIES, {5: "Old", 9: "New"}
    )
    (model,) = catalog.models
    assert model.item_names == ["Old", "New"]
    assert catalog.top_levels[0].subcategories[0].name == "Chairs/Sofas"
