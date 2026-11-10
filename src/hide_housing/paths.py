"""Game file paths for furniture models. See docs/furniture-paths.md."""

from __future__ import annotations

import logging

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


def model_paths(model_key: int) -> list[str]:
    """Return every game path to replace to hide this model.

    For now this is only the main ``.mdl``. Textures are left alone, and extra
    parts of multi-part furniture (``_b1``, ``...a.mdl``) are not handled yet; see
    docs/furniture-paths.md. Invalid keys are skipped with a warning and return [].
    """
    try:
        return [model_path(model_key)]
    except ValueError as exc:
        log.warning("Skipping furniture model: %s", exc)
        return []
