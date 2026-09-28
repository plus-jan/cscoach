"""CS2 economy rules engine driven by configs/economy_cs2.yaml (verify in M6.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cscoach.config import load_config


@dataclass(frozen=True)
class EconomyRules:
    start_money: int
    max_money: int
    round_win: dict[str, int]
    loss_bonus: tuple[int, ...]
    loss_counter_start: int
    loss_counter_on_win: str
    t_loss_after_plant_bonus: int
    kill_reward: dict[str, int]

    @classmethod
    def from_config(cls, cfg: dict[str, Any] | None = None) -> EconomyRules:
        c = cfg or load_config("economy_cs2")
        return cls(
            start_money=c["start_money"],
            max_money=c["max_money"],
            round_win=dict(c["round_win"]),
            loss_bonus=tuple(c["loss_bonus"]),
            loss_counter_start=c["loss_counter_start"],
            loss_counter_on_win=c["loss_counter_on_win"],
            t_loss_after_plant_bonus=c["t_loss_after_plant_bonus"],
            kill_reward=dict(c["kill_reward"]),
        )

    def loss_payout(self, loss_counter: int) -> int:
        """Money for a loss given the counter *after* incrementing for this loss."""
        i = max(0, min(loss_counter, len(self.loss_bonus) - 1))
        return self.loss_bonus[i]

    def next_loss_counter(self, counter: int, won: bool) -> int:
        top = len(self.loss_bonus) - 1
        if not won:
            return min(counter + 1, top)
        if self.loss_counter_on_win == "reset":
            return 0
        return max(counter - 1, 0)

    def kill_money(self, weapon_class: str) -> int:
        return self.kill_reward.get(weapon_class, self.kill_reward["default"])

    def team_round_income(
        self,
        *,
        won: bool,
        end_reason: str,
        loss_counter_before: int,
        side: str,
        bomb_planted: bool = False,
    ) -> tuple[int, int]:
        """(per-player income excluding kill rewards, new loss counter)."""
        new_counter = self.next_loss_counter(loss_counter_before, won)
        if won:
            return self.round_win[end_reason], new_counter
        income = self.loss_payout(new_counter)
        if side == "T" and bomb_planted:
            income += self.t_loss_after_plant_bonus
        return income, new_counter

    def clamp(self, money: int) -> int:
        return max(0, min(self.max_money, money))
