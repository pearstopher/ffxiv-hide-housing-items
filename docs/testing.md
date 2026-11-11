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
- [ ] Settings list the "<Tab>: Hide Categories" groups first (no Rugs group), then
      "Miscellaneous", then the "<Tab> – <Category>" groups
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
- [ ] **Rugs:** turn on *Miscellaneous → All rugs*. All rugs disappear.
- [ ] **Flowers:** turn on *Miscellaneous → All flowers and plants*. Flowers planted in
      flowerpots disappear and the pots stay.
- [ ] **Food:** turn on *Miscellaneous → All food*. All food disappears, both served and eaten.
- [ ] **Effects:** turn on *Miscellaneous → All housing effects*. Housing effects stop showing,
      and nothing errors or crashes.
- [ ] **Overlap:** turn on a category and one of its items together. The item stays hidden and
      nothing errors.

Changes never show while you're inside the house. After **every** option change, leave the
house and come back in before checking the result.

## Notes

- Multi-part furniture is hidden using the saved parts list (#40). If an item still leaves parts
  visible, open an issue. A part missing from the list can be fixed with `--refresh-parts`. Don't
  keep a list of individual items in this file.
- The Miscellaneous flowers, food and effects options (#41, #44, #49) are best guesses. If they miss something, open an issue.

## Results

| Date | Version | Tester | Result |
|---|---|---|---|
| 2026-11-10 | 0.1.0 | Ane Mora | Hide one category: pass. Hide one item: pass. Multi-part furniture (e.g. flower items, doors) keeps some parts visible; tracked in #35. |
| 2026-11-10 | 0.1.0 | Ane Mora | Tiny replacement model (#15, made via Penumbra glTF export/import + Blender): works. |
| 2026-11-10 | 0.1.0 | Ane Mora | Multi-part furniture (#40): pass, no remaining multi-part leftovers seen. Catch-all *All flowers and plants* (#41): pass. Catch-all *All food* (#44): pass. Flower Vases hide together with their flowers: pass. |
