import pytest

from cscoach.config import load_config
from cscoach.models.win_probability import GBDTWinProbability
from cscoach.schemas.tables import LEAKY_COLUMNS


@pytest.mark.parametrize("name", ["model_wp", "model_xk"])
def test_configs_have_no_leaky_features(name):
    feats = load_config(name)["features"]
    used = set(feats["numeric"]) | set(feats.get("categorical", []))
    assert not used & LEAKY_COLUMNS


def test_model_rejects_leaky_feature():
    cfg = load_config("model_wp")
    cfg["features"]["numeric"] = [*cfg["features"]["numeric"], "y_ct_win"]
    with pytest.raises(ValueError):
        GBDTWinProbability(cfg)
