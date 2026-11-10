# FFXIV Hide Housing Items

Generates a [Penumbra](https://github.com/xivdev/Penumbra) mod (`.pmp`) that lets you hide indoor
housing furniture, either a whole category at once or item by item. The furniture list comes
straight from the latest [datamining](https://github.com/xivapi/ffxiv-datamining), so a rebuild
picks up new furniture after each patch.

Nothing is hidden until you turn options on. Hidden furniture is currently swapped for a small
stand-in model rather than removed completely (see [Limitations](#limitations)).

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
Groups:        71 (1604 options)
Skipped:       3
Output:        ...\dist\hide-housing-furniture-0.1.0.pmp
```

"Skipped" lists furniture rows that have no item name in the game data.

| Option | What it does |
|---|---|
| `--refresh` | Re-download the datamining CSVs (otherwise the copy in `.cache/datamining/` is reused) |
| `--out DIR` | Write the `.pmp` to `DIR` instead of `dist/` |
| `--cache-dir DIR` | Keep downloaded CSVs in `DIR` instead of `.cache/datamining/` |
| `--replacement MDL` | Use your own `.mdl` instead of the bundled stand-in model |
| `-v`, `--verbose` | Show progress and warnings |

After a game patch, run `python -m hide_housing build --refresh` to pick up new furniture.

## Install in Penumbra

1. Open Penumbra (`/penumbra`) and go to the **Mods** tab.
2. Click **Import...** and choose the `.pmp`.
3. Select **Hide Housing Furniture**, enable it for the **Default** collection (it won't work in
   any other collection), and open its **Settings**.
4. Turn on what you want to hide:
   - **"<Tab>: hide whole categories"** groups (listed first): one option per category, such
     as *Tabletop: hide whole categories → Lighting*.
   - **"<Tab> – <Category>"** groups: one option per item, such as *Tabletop – Lighting →
     a specific lamp*. Large categories are split into "…, Part 1", "…, Part 2" groups, because
     Penumbra allows at most 32 options per group.
5. Leave the house and come back in. Changes never show while you're inside, so you have to
   do this after **every** change to the mod or its options.

Some items share one 3D model (for example "Sheep Dolls" and "Jumbo Sheep Dolls"). Their option
is named after the first item, the description lists the others, and hiding it hides all of them.

To update, build again and re-import the new `.pmp`.

## Limitations

- Hidden furniture is replaced with a small stand-in model rather than made fully invisible
  ([#15](https://github.com/pearstopher/ffxiv-hide-housing-items/issues/15)).
- Only each item's main model is replaced. Some furniture is built from more than one model, so
  parts of it can stay visible
  ([#35](https://github.com/pearstopher/ffxiv-hide-housing-items/issues/35)).
- Indoor furniture only. Outdoor (yard) furniture is not included.

## Development

```sh
pytest
```

- In-game test checklist: [docs/testing.md](docs/testing.md)
- How furniture maps to game files: [docs/furniture-paths.md](docs/furniture-paths.md)
- Penumbra mod format notes: [docs/penumbra-format.md](docs/penumbra-format.md)
