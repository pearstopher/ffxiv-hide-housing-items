# In-game test checklist

Automated tests (`pytest`) check the generated `meta.json` and `.pmp`. They can't check what
the game actually renders, so run this checklist by hand after changes that affect the mod's
output: paths, groups, the replacement model, or the Penumbra format.

## Setup

- [ ] `python -m hide_housing build` succeeds and prints a summary with `Skipped` near 0
- [ ] If a previous version is installed, remove it from Penumbra, then import the new `.pmp`
      with **Import...**
- [ ] Penumbra shows **Hide Housing Furniture** with no import warnings
- [ ] The mod is enabled for the **Default** collection (it won't work in any other)
- [ ] Settings list every "<Tab>: hide whole categories" group first, then the "<Tab> – <Category>" groups
- [ ] No group has more than 32 options. Penumbra would warn about ignored options otherwise.

## Behaviour (inside a house with furniture placed)

- [ ] **Off by default:** with the mod enabled and no options on, all furniture looks normal
- [ ] **Hide one category:** turn on one category option. Every item in that category is
      replaced, and items in other categories are not.
- [ ] **Hide one item:** turn off the category and turn on a single item option. Only that item
      (plus any items sharing its model, listed in the option description) is replaced.
- [ ] **Everything off again:** turn every option off. All furniture returns to normal.
- [ ] **Multi-part furniture:** hide a partition door and a canopy bed. Every part disappears
      (door and frame, bed and canopy).
- [ ] **Overlap:** turn on a category and one of its items together. The item stays hidden and
      nothing errors.

Changes never show while you're inside the house. After **every** option change, leave the
house and come back in before checking the result.

## Notes

- Some furniture is made of several models and may keep parts visible. That's a known general
  limitation tracked in [#35](https://github.com/pearstopher/ffxiv-hide-housing-items/issues/35),
  not a test failure. Don't list individual items; report it only if a whole new kind of
  breakage appears.

## Results

| Date | Version | Tester | Result |
|---|---|---|---|
| 2026-11-10 | 0.1.0 | Ane Mora | Hide one category: pass. Hide one item: pass. Multi-part furniture (e.g. flower items, doors) keeps some parts visible; tracked in #35. |
| 2026-11-10 | 0.1.0 | Ane Mora | Tiny replacement model (#15, made via Penumbra glTF export/import + Blender): works. |
