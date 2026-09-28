import numpy as np

from cscoach.config import load_config
from cscoach.models.training import train_wp
from cscoach.validation.metrics import expected_calibration_error, log_loss
from cscoach.validation.report import evaluate_probabilistic


def _cfg():
    cfg = load_config("model_wp")
    cfg["lightgbm"].update(n_estimators=300, learning_rate=0.05, min_child_samples=50)
    cfg["calibration"]["isotonic_min_rows"] = 3000
    return cfg


def test_wp_end_to_end_on_synthetic(synth_df):
    res = train_wp(synth_df, _cfg())
    t = res.test_frame
    y = t["y_ct_win"]
    # GBDT must beat baseline log-loss and be calibrated on held-out matches
    assert log_loss(y, t["p_wp"]) < log_loss(y, t["p_baseline"])
    assert expected_calibration_error(y, t["p_wp"]) < 0.04
    for tier, part in t.groupby("tier"):
        assert expected_calibration_error(part["y_ct_win"], part["p_wp"]) < 0.06, tier


def test_monotone_in_alive_ct(synth_df):
    res = train_wp(synth_df, _cfg())
    row = res.test_frame.iloc[[0]].copy()
    ps = []
    for a in range(1, 6):
        r = row.assign(alive_ct=a, man_advantage=a - row["alive_t"].iloc[0])
        ps.append(res.model.predict_raw(r)[0])
    assert np.all(np.diff(ps) >= -1e-9)


def test_report_structure(synth_df, tmp_path):
    res = train_wp(synth_df, _cfg())
    cfg = load_config("validation")
    cfg["bootstrap"]["n_resamples"] = 50
    cfg["gates"]["wp"]["min_rounds_per_stratum"] = 10
    rep = evaluate_probabilistic(
        res.test_frame,
        model="wp",
        y_col="y_ct_win",
        p_col="p_wp",
        baseline_col="p_baseline",
        validation_cfg=cfg,
    )
    assert "tier" in rep.strata and rep.gates
    assert rep.overall["ess_residual"] < rep.overall["n"]
    assert rep.write(tmp_path).exists()
