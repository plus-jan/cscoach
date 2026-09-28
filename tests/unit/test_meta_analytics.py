import numpy as np
import pandas as pd

from cscoach.validation.meta_analytics import discrimination, independence, stability


def _players(signal_sd: float, noise_sd: float, n_players=60, n_obs=40, seed=0):
    rng = np.random.default_rng(seed)
    true = rng.normal(0, signal_sd, n_players)
    rows = [
        {"player": i, "t": t, "v": true[i] + rng.normal(0, noise_sd)}
        for i in range(n_players)
        for t in range(n_obs)
    ]
    return pd.DataFrame(rows)


def test_signal_metric_is_discriminative_and_stable():
    df = _players(1.0, 1.0)
    assert discrimination(df, "player", "v") > 0.8
    assert stability(df, "player", "v", "t") > 0.8


def test_noise_metric_is_not():
    df = _players(0.0, 1.0)
    assert discrimination(df, "player", "v") < 0.3
    assert stability(df, "player", "v", "t") < 0.5


def test_independence():
    rng = np.random.default_rng(0)
    kd = rng.normal(size=200)
    t = pd.DataFrame({"kd": kd, "copy": 2 * kd + 1, "new": rng.normal(size=200)})
    assert independence(t, "copy", ["kd"]) < 0.01
    assert independence(t, "new", ["kd"]) > 0.9
