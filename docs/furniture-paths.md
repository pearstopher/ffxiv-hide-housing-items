# Furniture → game file paths

How a datamined indoor furniture item maps to the model file our mod replaces. Data is from
[xivapi/ffxiv-datamining](https://github.com/xivapi/ffxiv-datamining) `csv/en/`, as of 2026-11-10.

## Path format

```
bgcommon/hou/indoor/general/{NNNN}/bgparts/fun_b0_m{NNNN}.mdl
```

- `{NNNN}` is **`HousingFurniture.ModelKey`**, zero-padded to four digits (`633` → `0633`,
  `7` → `0007`). The largest key in the data is currently `1637`, so four digits are enough.
- Only the `.mdl` is replaced. Textures are left alone (see `example/meta.json`).

## The data chain

```
FurnitureCatalogCategory ──┐
  #, Category (name),      │ Category
  Unknown0 (= HousingItemCategory), Unknown1 (sort order)
                           │
FurnitureCatalogItemList ──┘
  #, Item, Category, Patch
        │ Item
        ▼
HousingFurniture                     Item
  #, Item, ModelKey,  ───────────►   #, Name, ...
  HousingItemCategory
        │ ModelKey
        ▼
  bgcommon/hou/indoor/general/{ModelKey:04d}/bgparts/fun_b0_m{ModelKey:04d}.mdl
```

Checked against the example. `HousingFurniture` row `197269` has `ModelKey 633` and `Item 21839`,
which is **"Stage Panel"**: catalog category 8, "Walls/Pillars/Partitions", under Furnishings. So
`fun_b0_m0633.mdl` in `example/meta.json` is the Stage Panel. The `0633` is the **model key, not
the item ID**: item 633 is a "Dated Hempen Tunic", and catalog row 633 is a different item.

### Columns

| Sheet | Column | Meaning |
|---|---|---|
| `HousingFurniture` | `Item` | Item ID (`0` = unused row) |
| | `ModelKey` | The `{NNNN}` in the path (`0` = unused row) |
| | `HousingItemCategory` | Top-level group: 12 Furnishings, 13 Tables, 14 Tabletop, 15 Wall-mounted, 16 Rugs |
| `FurnitureCatalogItemList` | `Item` / `Category` | Item ID → catalog subcategory |
| `FurnitureCatalogCategory` | `Category` | Subcategory name, e.g. "Tables", "Lighting" |
| | `Unknown0` | The top-level `HousingItemCategory` (12–16) this subcategory belongs to |
| | `Unknown1` | Sort order within that top-level group |
| `Item` | `Name` | Display name |

The top-level names (12–16) match the in-game housing tabs. They are not in these sheets, so we
hard-code them.

Subcategory names repeat across top-level groups ("Miscellaneous", "Lighting", "Plants",
"Interactive Furnishings", …), so labels must include the top level, e.g. "Tabletop – Lighting".

## Numbers (2026-11-10)

| | Count |
|---|---|
| `HousingFurniture` rows with an item | 1736 |
| …that are also in `FurnitureCatalogItemList` | 1331 |
| Distinct model keys | 1573 |
| Model keys shared by more than one item | 122 |
| Items with a blank name | 3 |
| Catalog subcategories | 30 |

## Edge cases

1. **Furniture missing from the catalog (≈400 items).** `FurnitureCatalogItemList` only lists
   items sold by the housing catalog NPC. Items from other sources (e.g. "Sheep Dolls") are
   only in `HousingFurniture`. **Recommendation:** use `HousingFurniture` as the master list;
   use the catalog subcategory when present, otherwise file the item under
   "<Top level> – Other".
2. **Shared model keys (122 keys).** Several items can use the same model, e.g. key 290 =
   "Sheep Dolls" and "Jumbo Sheep Dolls" (same model, scaled), and key 243 is shared by 30+
   retainer/vendor permits. Hiding one hides them all. **Recommendation:** make one option per
   model key and list every item name in the option label or description.
3. **Unused rows.** Skip rows where `Item` or `ModelKey` is `0`, and items with a blank name.
4. **Multi-part models (unverified).** Some furniture is built from several parts listed in its
   `.sgb` (e.g. `asset/fun_b0_m{NNNN}.sgb`), and a part may have a different filename such as
   `fun_b0_m{NNNN}a.mdl`, `_b1_`, or a model under another key. Replacing only
   `fun_b0_m{NNNN}.mdl` may leave such pieces visible. This needs game files to confirm, e.g.
   with Penumbra's resource logger or TexTools. For now, code generates only the main path, and
   in-game testing (#14) should note any items that don't fully disappear.
5. **Items outside `indoor/general`.** All indoor furniture checked so far uses
   `indoor/general/`. Outdoor furniture is in a different sheet (`HousingYardObject`), which is
   out of scope.

## Test fixtures

`tests/fixtures/` contains real rows trimmed from these CSVs: Riviera Round Table (key 1),
Stage Panel (key 633), Sheep Dolls + Jumbo Sheep Dolls (shared key 290, not in the catalog),
an unused row, and the full category sheet. `tests/test_furniture_paths_data.py` checks the
chain above against them.

## Catalog vs. HousingItemCategory

One item disagrees between the two sources: "Lattice-windowed Cabinet" (model 1466) has
`HousingItemCategory` 13 (Tables) but is listed in the catalog under Furnishings ›
Shelves/Chests. When an item is in the catalog, `catalog.py` uses the catalog's subcategory
**and its top level**, because that is where players find it in game. Only items missing from
the catalog fall back to `HousingItemCategory` + "Other".
