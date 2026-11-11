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
   "<Top level> – Other". Exception: a tab with only one subcategory (Rugs) has no "Other";
   uncatalogued rugs go straight into "Rugs – Rugs".
2. **Shared model keys (122 keys).** Several items can use the same model, e.g. key 290 =
   "Sheep Dolls" and "Jumbo Sheep Dolls" (same model, scaled), and key 243 is shared by 30+
   retainer/vendor permits. Hiding one hides them all. **Recommendation:** make one option per
   model key and list every item name in the option label or description.
3. **Unused rows.** Skip rows where `Item` or `ModelKey` is `0`, and items with a blank name.
4. **Multi-part furniture.** Confirmed in game: some furniture keeps parts visible when only
   `fun_b0_m{NNNN}.mdl` is replaced. Researched in #35; see
   [Multi-part furniture](#multi-part-furniture-35) below.
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

## Multi-part furniture (#35)

In-game testing showed two kinds of leftover parts after hiding an item: **doors** (the frame is
hidden, the door leaf stays) and **interactable flower items** (the pot or vase is hidden, the
flowers stay). Researched 2026-11-10.

### Data source: ResLogger2 path list

[ResLogger2](https://github.com/perchbirdd/ResLogger2) collects game file paths that players'
clients have loaded and publishes them. The current-patch list is at
`https://rl2.perchbird.dev/download/export/CurrentPathList.gz` (~8 MB gzip, ~1.8 M paths, one per
line). The URL comes from a tool that uses it:
[NotNite/Alpha `PathListService.cs`](https://github.com/NotNite/Alpha/blob/main/Alpha/Services/PathListService.cs).
The list only contains paths someone has seen, so it is **incomplete**. Of our 1,570 models,
1,559 have at least one `.mdl` listed, and 1,509 have their main `fun_b0_m{NNNN}.mdl` listed.

### Finding 1: extra parts sit next to the main model (doors, beds, partitions…)

Every `.mdl` for indoor furniture in the list lives in `bgcommon/hou/indoor/general/{NNNN}/bgparts/`.
**307 models** have more `.mdl` files there besides `fun_b0_m{NNNN}.mdl`, almost always with a
letter suffix:

| File name pattern | Models |
|---|---|
| `fun_b0_m{NNNN}a.mdl` | 281 |
| `fun_b0_m{NNNN}b.mdl` | 134 |
| `fun_b0_m{NNNN}c.mdl` … `g`, up to `s` | fewer |
| other prefixes (`bds_t4_…`, `bks_t4_…`) | 7 (keys 0413–0415, 0472–0475) |

Examples:
- Doors: Mahogany Partition Door (0405) → `fun_b0_m0405a.mdl`; Factory Automatic Door (0974)
  → `a`–`d`
- Beds: Eastern and Tropical Canopy Beds (1113, 1408) → `a`
- Kitchen Cabinet (1380) → 17 parts

This matches the door observation: the main model is the frame, and the moving door is a
separate part.

**Bulk method (implemented in #40):** for each model, replace **every** `.mdl` listed under its
`bgparts/` folder. The path list is not downloaded on each build. `hide_housing.parts` extracted
the extra part names once into `src/hide_housing/data/model_parts.json` (308 keys, 704 files;
307 of them are current furniture models). Builds read that file, and
`build --refresh-parts` downloads the list again and rewrites the file only if the parts changed.
Limitation: parts nobody has loaded yet are missing from the list. No speculative (unlisted)
suffixes are added, because nothing confirms that unused redirects are harmless.

### Finding 2: flowerpot flowers are shared gardening models

`HousingFurniture.UsageType` marks furniture that displays *other* content:

| UsageType | Furniture | Content |
|---|---|---|
| 11 | Riviera / Glade / Oasis Flowerpot (3) | planted flowers |
| 12 | vases, picture frames (34) | the item displayed in them |
| 13 | aquariums (8) | fish (`bgcommon/hou/indoor/gyo/…`) |
| 15 | mannequin | character gear |

Flowerpot flowers are gardening models. `GardeningSeed` rows with `IsPlantPotFlowerSeed = True`
(27 seeds) have `ModelID` 101+, which matches `bgcommon/hou/outdoor/frm/{ModelID:04d}/bgparts/*.mdl`
in the path list. These models belong to the **seed, not the pot**, so the same flower shows in
every flowerpot.

**Implemented in #41: one catch-all option, "All flowers and plants" (best guess).**
- **Which seeds:** datamined. All 34 `GardeningSeed` `ModelID`s: crops, shards (crystals can be
  planted, confirmed by the user), and the 27 flowerpot seeds.
- **Which files:** a pattern derived from ResLogger2, which the user approved for plant and food
  model guesses only:
  - every seed: `frm_f{1-5}_m0{ID:03d}.mdl`
  - flowerpot seeds also: `frm_f4_m{1-9}{ID:03d}.mdl` and `han_f4_m{0-9}{ID:03d}.mdl`
- **Coverage:** the pattern gives 683 paths. That covers all 668 gardening models in the path
  list, plus 15 guessed gaps, and the 3 paths the user captured in game with Penumbra's Resource
  Logger.
- **Outdoors:** outdoor garden plots use the same models, so they may be hidden there too.
- **No per-flower options,** by request.

**Implemented in #44: one catch-all option, "All food" (best guess).**
- **Which models:** datamined. `HousingFurniture` rows with `UsageType` 7, currently 98 models.
- **Which files:** for each model, the main `fun_b0_m{NNNN}.mdl`, plus `…a.mdl` and `…b.mdl` (food
  has two states, served and eaten), plus any extra parts in the saved multi-part list (#40).
  That's 326 paths, covering all 247 food model files in the ResLogger2 list plus 79 guessed
  states. ResLogger2 was approved by the user for plant and food model guesses only.
- **No per-food options in the catch-all,** by request.

**Vase flowers:** the user's capture showed the Riviera and Glade *Flower Vase* (keys 0143, 0145)
loading `han_f4_m0001.mdl` and `han_f4_m0003.mdl` from their own furniture folders. Those are
already extra parts in the saved multi-part list (#40), so hiding the vase hides its flowers.
Picture-frame contents and the display vases (UsageType 12) weren't traced. Aquarium fish and
mannequin gear are out of scope: they are separate items, not part of the furniture.
