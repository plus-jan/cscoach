import pandas as pd
import pytest

from cscoach.economy.rules import EconomyRules
from cscoach.valuation.credit import shapley_values
from cscoach.valuation.wpa import attribute_kill_credit, event_wpa


def test_event_wpa_perspective():
    ev = pd.DataFrame(
        {"team_side": ["CT", "T"], "wp_ct_before": [0.5, 0.5], "wp_ct_after": [0.7, 0.3]}
    )
    out = event_wpa(ev)
    assert out["wpa"].tolist() == pytest.approx([0.2, 0.2])


def test_kill_credit_sums_to_wpa():
    c = attribute_kill_credit(0.2, "a", assister="b")
    assert sum(c.values()) == pytest.approx(0.2)
    assert c["a"] > c["b"]


def test_shapley_efficiency_and_symmetry():
    def v(s):
        return 0.1 * len(s) + (0.2 if {"a", "b"} <= s else 0.0)

    phi = shapley_values(["a", "b", "c"], v)
    assert sum(phi.values()) == pytest.approx(v({"a", "b", "c"}) - v(frozenset()))
    assert phi["a"] == pytest.approx(phi["b"])
    assert phi["c"] == pytest.approx(0.1)


def test_economy_loss_bonus_progression():
    r = EconomyRules.from_config()
    counter = r.loss_counter_start
    incomes = []
    for _ in range(5):
        inc, counter = r.team_round_income(
            won=False, end_reason="elimination", loss_counter_before=counter, side="CT"
        )
        incomes.append(inc)
    assert incomes == sorted(incomes) and incomes[-1] == r.loss_bonus[-1]
    inc, counter2 = r.team_round_income(
        won=True, end_reason="bomb_defused", loss_counter_before=counter, side="CT"
    )
    assert inc == r.round_win["bomb_defused"] and counter2 == counter - 1
