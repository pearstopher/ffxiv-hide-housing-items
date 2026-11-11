# Penumbra `.pmp` format

What this project's generator needs to know about Penumbra mod packs. Verified against
Penumbra's `testing` branch at commit `d0cab787b8` (2026-11-03). See [Sources](#sources).

## The file itself

A `.pmp` is a plain zip archive with the extension changed. Penumbra extracts it into its
mod directory as-is. Layout for this project:

```
meta.json          <- everything: mod info, default data, all option groups
files/
  replacement.mdl  <- replacement asset referenced from meta.json
```

## Target: `FileVersion` 4 (single `meta.json`)

`FileVersion` 4 is the current version (`ModMeta.CurrentFileVersion = 4`). In v4, **everything
lives in `meta.json`**: `DefaultData` and `Groups` are inline. `example/meta.json` already uses
this layout.

The older v3 layout split the data across `meta.json`, `default_mod.json` and one
`group_NNN_<name>.json` per group. Penumbra still reads v3 and migrates it to v4 on load, but
we generate v4 directly. A v4 mod with a higher `FileVersion` than the installed Penumbra
supports is rejected.

### `meta.json` fields we use

| Field | Notes |
|---|---|
| `FileVersion` | Required. Always `4`. |
| `Name` | Required. Non-empty. |
| `Identifier` | GUID. "Currently not used" by Penumbra, but keep it stable across builds. |
| `Author`, `Description`, `Version`, `Website` | Optional strings. `Version` is free-form. |
| `LastWrite` | UTC ISO-8601 time. Written by Penumbra; optional for us. |
| `DefaultData` | A container (see below) that is always applied while the mod is enabled. **Must stay empty for this project**, or items are hidden for everyone with no way to opt out. |
| `Groups` | Array of option groups. |

## Containers (`DefaultData` and every option)

| Field | Meaning |
|---|---|
| `Files` | `{ "<game path>": "<relative file in the mod>" }`: replace a game file with a file we ship. |
| `FileSwaps` | `{ "<game path>": "<other game path>" }`: redirect a game file to **another existing game file**. No file has to be shipped. Worth considering for #15. |
| `Manipulations` | Meta edits. Not needed here. |

Paths:
- **Game paths (keys)** use forward slashes and must not start with `/`, `\`, `.`, `:` or `?`,
  e.g. `bgcommon/hou/indoor/general/0633/bgparts/fun_b0_m0633.mdl`.
- **File paths (values)** are relative to the mod root. Penumbra writes Windows backslashes
  (`"files\\table_mat.mdl"` in JSON); the schema accepts either separator, but we match
  Penumbra and use backslashes.

## Groups

| Field | Notes |
|---|---|
| `Name` | Required. Shown in the UI. |
| `Type` | Required. `Single`, `Multi`, `Imc` or `Combining`. We use **`Multi`**. |
| `Id` | GUID, unique within the mod. |
| `Priority` | Integer. If several groups change the same file, the **highest priority wins**. |
| `DefaultSettings` | Integer. Meaning depends on `Type` (below). |
| `Description` | Optional. |
| `Options` | Array of options. Each option is a container plus `Name`, `Id`, optional `Description`, and (Multi only) `Priority`. |

Optional UI fields that could help with a long list:
- **Group `Layout`** flags: `Hide`, `Space`, `ParentHeader`, `DefaultClosed`
- **Group `ParentSetting`**: nests a group under another group or option
- **Option `Layout`** flags: `Hide`, `Separator`, `HideOptionLabel`, `Space`

### `DefaultSettings`

- **Multi**: a bitmask, where bit *i* enables option *i*. `0` = all off. The example's `1`
  means "first option on". **We always use `0`.**
- **Single**: the index of the selected option.

### Option limits

| Group type | Limit |
|---|---|
| **Multi** | **32 options** (`IModGroup.MaxMultiOptions`). With FileVersion 4, any options past the 32nd are **silently ignored** at load time (a warning notification at best). Penumbra only auto-splits over-limit groups when it imports old v3 group files from a `.pmp`, so **we must split groups ourselves**. Penumbra names split groups `"<name>, Part N"`; we follow the same convention. |
| Combining | 8 options (2^n containers). Not used. |
| Single | No limit found in the loader. Not used. |

### Conflicts and priority

- Within the mod, when two enabled options change the same game path, the higher group
  `Priority` wins. Within one Multi group, the higher option `Priority` wins.
- In this project every hiding option maps a path to the **same** replacement, so overlap
  between the category toggles (#10) and the per-item toggles (#11) is harmless: whichever
  wins, the item is hidden.
- Across different mods, the per-mod priority set in Penumbra's UI decides.

## Generator rules (summary)

1. Write a single `meta.json` with `FileVersion: 4`, inline `Groups`, and an empty `DefaultData`.
2. Use only `Multi` groups, each with at most 32 options and `DefaultSettings: 0`.
3. Split larger lists into `"<name>, Part 1"`, `"<name>, Part 2"`, … groups.
4. Game paths use forward slashes; mod file paths use `files\\<name>`.
5. Keep `Id`s deterministic so rebuilds diff cleanly (see #9).

These numbers live in code as constants in `src/hide_housing/penumbra.py`.

## Sources

Penumbra repository: https://github.com/xivdev/Penumbra (branch `testing`)
- `schemas/mod_meta-v4.json`, `schemas/group.json`, `schemas/structs/{group_multi,group_single,option,container}.json`: field definitions
- `Penumbra/Mods/Groups/IModGroup.cs`: `MaxMultiOptions = 32`, `MaxCombiningOptions = 8`
- `Penumbra/Files/GroupDeserialization.cs`: excess Multi options are ignored on load
- `Penumbra/Files/ModDeserialization.cs`: v3 → v4 migration (`MigrateGroups`)
- `Penumbra/Mods/ModCreator.cs`: auto-split of over-limit groups only on v3 `.pmp` import
- `Penumbra/Mods/Settings/Setting.cs`: Multi = bitmask, Single = index
