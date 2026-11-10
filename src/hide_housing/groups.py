"""Turn the furniture catalog into Penumbra option groups."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from hide_housing import penumbra
from hide_housing.catalog import Catalog, FurnitureModel, TopLevel
from hide_housing.meta import multi_group, option
from hide_housing.paths import model_paths

CATEGORY_GROUP_PRIORITY = 0


def hide_files(models: Iterable[FurnitureModel], replacement: str) -> dict[str, str]:
    """``{game path: replacement}`` for every file of every model."""
    return {path: replacement for model in models for path in model_paths(model.model_key)}


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
    return f"{top.name}: hide whole categories"


def category_groups(catalog: Catalog, replacement: str) -> list[dict[str, Any]]:
    """One group per top-level tab, with one option per subcategory.

    Turning an option on hides every furniture model in that subcategory.
    Subcategory names repeat across tabs ("Miscellaneous"), so the tab is part of
    the group name. All options are off by default.
    """
    groups: list[dict[str, Any]] = []
    for top in catalog.top_levels:
        name = category_group_name(top)
        options = []
        for sub in top.subcategories:
            files = hide_files(sub.models, replacement)
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
