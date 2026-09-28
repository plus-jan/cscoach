import numpy as np
import pytest

from cscoach.validation import metrics as m


def test_perfect_and_constant_predictions():
    y = np.array([0, 1, 1, 0])
    assert m.brier_score(y, y) == 0
    assert m.brier_score(y, np.full(4, 0.5)) == pytest.approx(0.25)
    assert m.log_loss(y, np.full(4, 0.5)) == pytest.approx(np.log(2))


def test_ece_near_zero_for_calibrated_and_large_for_biased():
    rng = np.random.default_rng(0)
    p = rng.uniform(size=50_000)
    y = (rng.uniform(size=p.size) < p).astype(int)
    assert m.expected_calibration_error(y, p) < 0.01
    assert m.expected_calibration_error(y, np.clip(p + 0.15, 0, 1)) > 0.1


def test_brier_skill_positive_when_better():
    rng = np.random.default_rng(1)
    p = rng.uniform(size=5000)
    y = (rng.uniform(size=p.size) < p).astype(int)
    assert m.brier_skill_score(y, p, np.full(p.size, y.mean())) > 0


def test_rejects_bad_input():
    with pytest.raises(ValueError):
        m.brier_score([0, 1], [0.5, 1.5])
