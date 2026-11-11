# Making a release

Releases are published on GitHub with the built `.pmp` and the preset files attached, so players
can download the mod without building it.

## 1. Pick the version

Versions are `MAJOR.MINOR.PATCH`. Bump:
- **PATCH** for fixes and data refreshes (e.g. new furniture after a game patch)
- **MINOR** for new options or features
- **MAJOR** for changes that break existing settings or presets

Set the same version in **both** `pyproject.toml` (`version`) and `src/hide_housing/__init__.py`
(`__version__`). `tests/test_smoke.py` fails if they differ. Do the bump through an issue, branch
and PR like any other change.

## 2. Update the data (after a game patch)

```sh
python -m hide_housing build --refresh --refresh-parts
```

- `--refresh` downloads the latest datamining CSVs into `.cache/datamining/`.
- `--refresh-parts` re-downloads the ResLogger2 path list and updates the saved
  `src/hide_housing/data/model_parts.json` and `housing_vfx.json` only if they changed. Commit any
  changes through a PR.
- After a patch, check the presets in `presets/` still match (see #59): items can move between
  ", Part N" groups.

## 3. Test

```sh
pytest
```

Then run the in-game checklist in [testing.md](testing.md) with the new `.pmp`, and record the
results there.

## 4. Build the release file from `master`

```sh
git checkout master
git pull
python -m hide_housing build --refresh
```

This writes `dist/hide-housing-furniture-<version>.pmp`. The summary must show the new version in
the file name.

## 5. Publish

```sh
gh release create v<version> \
  dist/hide-housing-furniture-<version>.pmp \
  presets/hide-everything.txt \
  presets/rainbow-cafe.txt \
  --target master --title "v<version>" --notes-file <notes.md>
```

The release notes should cover what changed, how to install (link to the README), and the
presets. `gh release create` also creates the `v<version>` tag on `master`.

Check the release page afterwards: the `.pmp` must download and import in Penumbra.
