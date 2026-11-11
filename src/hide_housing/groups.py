"""Turn the furniture catalog into Penumbra option groups."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from hide_housing import penumbra
from hide_housing.catalog import Catalog, FurnitureModel, Subcategory, TopLevel
from hide_housing.meta import multi_group, option
from hide_housing.paths import model_paths

# Category and item options redirect to the same replacement, so overlaps are
# harmless (see docs/penumbra-format.md). Item groups get a higher priority so
# they would win if the two ever diverge (e.g. per-item replacements later).
CATEGORY_GROUP_PRIORITY = 0
ITEM_GROUP_PRIORITY = 1


# {model key: extra .mdl names in its bgparts folder}; see hide_housing.parts
Parts = Mapping[int, Sequence[str]]


def hide_files(models: Iterable[FurnitureModel], replacement: str, parts: Parts | None = None) -> dict[str, str]:
    """``{game path: replacement}`` for every file of every model, including any
    extra model parts listed in ``parts``."""
    parts = parts or {}
    return {
        path: replacement
        for model in models
        for path in model_paths(model.model_key, parts.get(model.model_key, ()))
    }


def split_multi_groups(
    name: str,
    options: Sequence[dict[str, Any]],
    priority: int = 0,
    description: str = "",
) -> list[dict[str, Any]]:
    """One Multi group, or ``"<name>, Part N"`` groups of at most 32 options each.

    Uses Penumbra's own naming for split groups. Build ``options`` with the base
    ``name`` so option IDs stay the same if an option moves to another part.
    """
    size = penumbra.MAX_MULTI_OPTIONS
    if len(options) <= size:
        return [multi_group(name, options, priority, description)]
    chunks = [options[i:i + size] for i in range(0, len(options), size)]
    return [
        multi_group(f"{name}, Part {n}", chunk, priority, description)
        for n, chunk in enumerate(chunks, start=1)
    ]


def category_group_name(top: TopLevel) -> str:
    return f"{top.name}: Hide Categories"


def category_groups(
    catalog: Catalog,
    replacement: str,
    parts: Parts | None = None,
    min_subcategories: int = 1,
) -> list[dict[str, Any]]:
    """One group per top-level tab, with one option per subcategory.

    Turning an option on hides every furniture model in that subcategory.
    Subcategory names repeat across tabs ("Miscellaneous"), so the tab is part of
    the group name. All options are off by default. Tabs with fewer than
    ``min_subcategories`` subcategories are skipped; the mod uses 2 so that a
    single-category tab (Rugs) goes to Miscellaneous instead (``single_category_specs``).
    """
    groups: list[dict[str, Any]] = []
    for top in catalog.top_levels:
        if len(top.subcategories) < min_subcategories:
            continue
        name = category_group_name(top)
        options = []
        for sub in top.subcategories:
            files = hide_files(sub.models, replacement, parts)
            if not files:
                continue
            count = len(sub.models)
            description = (
                f"Hides all {count} furniture model{'s' if count != 1 else ''} "
                f"in {top.name} > {sub.name}."
            )
            options.append(option(name, sub.name, files, description))
        if options:
            groups.extend(split_multi_groups(
                name,
                options,
                CATEGORY_GROUP_PRIORITY,
                f"Hide every item in a {top.name} category at once.",
            ))
    return groups


def single_category_specs(
    catalog: Catalog, replacement: str, parts: Parts | None = None
) -> list[tuple[str, list[str], str]]:
    """Bulk options for tabs with only one subcategory (currently Rugs), as
    ``(name, game paths, description)`` for the Miscellaneous group."""
    specs = []
    for top in catalog.top_levels:
        if len(top.subcategories) != 1:
            continue
        paths = list(hide_files(top.subcategories[0].models, replacement, parts))
        if paths:
            label = top.name.lower()
            specs.append((f"All {label}", paths, f"Hides all {label}."))
    return specs


def item_group_name(top: TopLevel, sub: Subcategory) -> str:
    return f"{top.name} – {sub.name}"


def model_option(
    group_name: str, model: FurnitureModel, label: str, replacement: str, parts: Parts | None = None
) -> dict[str, Any] | None:
    """Option hiding one furniture model, or None if it has no valid paths."""
    files = hide_files([model], replacement, parts)
    if not files:
        return None
    description = also_hides_description(model.item_names[1:])
    return option(group_name, label, files, description, id_key=f"model {model.model_key}")


MAX_DESCRIPTION_LENGTH = 100


def also_hides_description(others: Sequence[str]) -> str:
    """One short sentence naming the other items that share a model.

    Lists as many names as fit in ``MAX_DESCRIPTION_LENGTH`` characters and
    summarises the rest as "and N more".
    """
    if not others:
        return ""
    full = f"Also hides: {', '.join(others)} (same model)."
    if len(full) <= MAX_DESCRIPTION_LENGTH:
        return full
    shown = 0
    while shown < len(others):
        more = len(others) - (shown + 1)
        candidate = f"Also hides: {', '.join(others[:shown + 1])} and {more} more (same model)."
        if len(candidate) > MAX_DESCRIPTION_LENGTH:
            break
        shown += 1
    if shown == 0:
        return f"Also hides {len(others)} other items (same model)."
    return f"Also hides: {', '.join(others[:shown])} and {len(others) - shown} more (same model)."


def item_groups(catalog: Catalog, replacement: str, parts: Parts | None = None) -> list[dict[str, Any]]:
    """One group per subcategory with one option per furniture model.

    Options are named after the model's first item; other items sharing the
    model are listed in the description. Large subcategories are split into
    ``"<name>, Part N"`` groups of at most 32 options. All options start off.
    """
    groups: list[dict[str, Any]] = []
    for top in catalog.top_levels:
        for sub in top.subcategories:
            name = item_group_name(top, sub)
            name_counts = Counter(m.name for m in sub.models)
            options = []
            for model in sub.models:
                label = model.name
                if name_counts[label] > 1:  # keep option names unique within a group
                    label = f"{label} (model {model.model_key:04d})"
                opt = model_option(name, model, label, replacement, parts)
                if opt is not None:
                    options.append(opt)
            if options:
                groups.extend(split_multi_groups(
                    name,
                    options,
                    ITEM_GROUP_PRIORITY,
                    f"Hide individual {top.name} > {sub.name} items.",
                ))
    return groups


def all_groups(
    catalog: Catalog,
    replacement: str,
    parts: Parts | None = None,
    catch_all: Sequence[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Every group in UI order: all bulk groups first (the per-tab "Hide
    Categories" groups, then the ``catch_all`` groups, i.e. Miscellaneous), then
    all individual item groups (in tab/subcategory order)."""
    return (
        category_groups(catalog, replacement, parts, min_subcategories=2)
        + list(catch_all)
        + item_groups(catalog, replacement, parts)
    )
