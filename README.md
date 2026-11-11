# FFXIV Hide Housing Items

Generates a [Penumbra](https://github.com/xivdev/Penumbra) mod (`.pmp`) that lets you hide indoor
housing furniture, either a whole category at once or item by item. The furniture list comes
straight from the latest [datamining](https://github.com/xivapi/ffxiv-datamining), so a rebuild
picks up new furniture after each patch.

Nothing is hidden until you turn options on. Hidden furniture is swapped for a tiny replacement
model so it no longer shows (see [Limitations](#limitations) for furniture made of several parts).

## Build the mod

Requires Python 3.11 or newer.

```sh
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# macOS/Linux:          source .venv/bin/activate
pip install -e ".[dev]"

python -m hide_housing build
```

This writes `dist/hide-housing-furniture-<version>.pmp` and prints a summary like:

```
Tabs:          5
Categories:    34
Models:        1570
Items:         1733
Groups:        73 (1607 options)
Multi-part:    307 models (+697 extra part files)
Housing VFX:   281 effects
Parts list:    saved file
Skipped:       3
Output:        ...\dist\hide-housing-furniture-0.1.0.pmp
```

"Skipped" lists furniture rows that have no item name in the game data. "Multi-part" counts
furniture made of several models (doors, canopy beds, partitions…), all of whose parts are hidden
(see [Multi-part furniture](#multi-part-furniture)).

| Option | What it does |
|---|---|
| `--refresh` | Re-download the datamining CSVs (otherwise the copy in `.cache/datamining/` is reused) |
| `--out DIR` | Write the `.pmp` to `DIR` instead of `dist/` |
| `--cache-dir DIR` | Keep downloaded CSVs in `DIR` instead of `.cache/datamining/` |
| `--replacement MDL` | Use your own `.mdl` instead of the bundled replacement model |
| `--refresh-parts` | Re-download the game path list and update the saved multi-part and indoor VFX lists if they changed |
| `-v`, `--verbose` | Show progress and warnings |

After a game patch, run `python -m hide_housing build --refresh` to pick up new furniture.

### Multi-part furniture

Some furniture is made of several models next to each other, e.g. a door's frame
(`fun_b0_m0405.mdl`) and the door itself (`fun_b0_m0405a.mdl`). The extra parts come from the
[ResLogger2](https://github.com/perchbirdd/ResLogger2) game path list. That list is large
(~8 MB), so it is **not** downloaded on each build: the extra part names were extracted once and
saved in `src/hide_housing/data/model_parts.json`, which every build reads.

After a patch that adds new multi-part furniture, update the saved list with:

```sh
python -m hide_housing build --refresh-parts
```

This downloads the path list once and rewrites `model_parts.json` only if the parts changed. The
summary shows `refreshed, saved file updated` or `refreshed, no changes`. Commit the updated file.

### Housing effects

The *Miscellaneous → All housing effects* option uses a second saved list,
`src/hide_housing/data/housing_vfx.json`: every `.avfx` effect in the same path list under these
`bgcommon/hou/common/` folders: `vfx_hou_ind1`, `vfx_hou_dyna1`, `vfx_hou_com1` and
`vfx_hou_craft1`. The outdoor folder, `vfx_hou_out1`, is not included. The list is refreshed by
the same `--refresh-parts` download. Each effect is redirected to
`vfx/path/nothing.avfx`, a file that doesn't exist, so it fails to load. That's the technique
the [EasyEyes](https://github.com/0ceal0t/EasyEyes) plugin uses to remove effects.

## Install in Penumbra

1. Open Penumbra (`/penumbra`) and go to the **Mods** tab.
2. Click **Import...** and choose the `.pmp`.
3. Select **Hide Housing Furniture**, enable it for the **Default** collection (it won't work in
   any other collection), and open its **Settings**.
4. Turn on what you want to hide:
   - **"<Tab>: Hide Categories"** groups (listed first): one option per category, such as
     *Tabletop: Hide Categories → Lighting*. Rugs has only one category, so it is in
     Miscellaneous instead.
   - **"Miscellaneous"**: single switches that each hide a whole kind of thing, with no
     individual options:
     - *All rugs*
     - *All flowers and plants*: everything grown from gardening seeds, including flowers
       planted in flowerpots
     - *All food*: every food and drink item, served or eaten
     - *All housing effects*: every housing visual effect (VFX) in the saved effect list (see
       [Housing effects](#housing-effects))

     The flowers, food and effects lists are best guesses and may not be perfect.
   - **"<Tab> – <Category>"** groups: one option per item, such as *Tabletop – Lighting →
     a specific lamp*. Large categories are split into "…, Part 1", "…, Part 2" groups, because
     Penumbra allows at most 32 options per group.
5. Leave the house and come back in. Changes never show while you're inside, so you have to
   do this after **every** change to the mod or its options.

Some items share one 3D model (for example "Sheep Dolls" and "Jumbo Sheep Dolls"). Their option
is named after the first item, the description lists the others, and hiding it hides all of them.

To update, build again and re-import the new `.pmp`.

## Limitations

- Multi-part furniture is only fully hidden if all its parts are in the game path list, which only
  includes files players have loaded. Content shown *in* furniture (e.g. flowers planted in a
  flowerpot) belongs to a different item and isn't hidden
  ([#41](https://github.com/pearstopher/ffxiv-hide-housing-items/issues/41)).
- Indoor furniture only. Outdoor (yard) furniture is not included.

## Development

```sh
pytest
```

- In-game test checklist: [docs/testing.md](docs/testing.md)
- How furniture maps to game files: [docs/furniture-paths.md](docs/furniture-paths.md)
- Penumbra mod format notes: [docs/penumbra-format.md](docs/penumbra-format.md)
