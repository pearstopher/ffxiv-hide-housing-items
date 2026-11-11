import logging

import pytest

from hide_housing.paths import model_path, model_paths

def test_633_matches_the_original_test_mod():
    # The path replaced by the user's original hand-made test mod, which worked in game.
    assert model_path(633) == "bgcommon/hou/indoor/general/0633/bgparts/fun_b0_m0633.mdl"


@pytest.mark.parametrize(
    "key, padded",
    [(1, "0001"), (7, "0007"), (42, "0042"), (633, "0633"), (1637, "1637"), (9999, "9999")],
)
def test_zero_padded_to_four_digits(key, padded):
    assert model_path(key) == f"bgcommon/hou/indoor/general/{padded}/bgparts/fun_b0_m{padded}.mdl"


def test_only_mdl_paths():
    assert all(p.endswith(".mdl") for p in model_paths(633))
    assert model_paths(633) == [model_path(633)]


@pytest.mark.parametrize("key", [0, -1, 10000])
def test_invalid_keys_raise(key):
    with pytest.raises(ValueError):
        model_path(key)


def test_invalid_keys_are_skipped_with_warning(caplog):
    with caplog.at_level(logging.WARNING):
        assert model_paths(10000) == []
    assert "model key must be 1-9999, got 10000" in caplog.text
