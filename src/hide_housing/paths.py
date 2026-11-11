"""Game file paths for furniture models. See docs/furniture-paths.md."""

from __future__ import annotations

import logging
from collections.abc import Sequence

log = logging.getLogger(__name__)

MODEL_PATH_TEMPLATE = "bgcommon/hou/indoor/general/{key}/bgparts/fun_b0_m{key}.mdl"
MAX_MODEL_KEY = 9999  # keys are written as exactly four digits


def model_path(model_key: int) -> str:
    """Return the main ``.mdl`` game path for a ``HousingFurniture.ModelKey``.

    The key is zero-padded to four digits: 633 -> ``.../0633/bgparts/fun_b0_m0633.mdl``.
    Raises ValueError for keys that can't be written as four digits.
    """
    if not 1 <= model_key <= MAX_MODEL_KEY:
        raise ValueError(f"model key must be 1-{MAX_MODEL_KEY}, got {model_key}")
    return MODEL_PATH_TEMPLATE.format(key=f"{model_key:04d}")


def model_paths(model_key: int, extra_parts: Sequence[str] = ()) -> list[str]:
    """Return every game path to replace to hide this model.

    Always the main ``fun_b0_m{NNNN}.mdl``, plus ``extra_parts``: other ``.mdl``
    file names in the same ``bgparts`` folder (e.g. ``fun_b0_m0405a.mdl``, a door
    leaf), taken from the saved parts list (see hide_housing.parts). Textures are
    left alone. Invalid keys are skipped with a warning and return [].
    """
    try:
        main = model_path(model_key)
    except ValueError as exc:
        log.warning("Skipping furniture model: %s", exc)
        return []
    folder = main.rsplit("/", 1)[0]
    paths = [main]
    for name in extra_parts:
        path = f"{folder}/{name}"
        if path not in paths:
            paths.append(path)
    return paths
