"""Machine-readable data contracts. Keep in sync with docs/specs/02_data_contracts.md."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


class ContractError(ValueError):
    """Raised when a DataFrame violates its table contract."""


@dataclass(frozen=True)
class Column:
    name: str
    kind: str  # "int" | "float" | "str" | "bool" | "datetime" | "any"
    nullable: bool = False
    allowed: tuple[object, ...] | None = None


@dataclass(frozen=True)
class TableSchema:
    name: str
    columns: tuple[Column, ...]
    primary_key: tuple[str, ...] = field(default_factory=tuple)

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]


_KIND_CHECKS = {
    "int": pd.api.types.is_integer_dtype,
    "float": pd.api.types.is_numeric_dtype,
    "bool": lambda s: pd.api.types.is_bool_dtype(s) or pd.api.types.is_integer_dtype(s),
    "str": lambda s: pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s),
    "datetime": pd.api.types.is_datetime64_any_dtype,
    "any": lambda s: True,
}


def validate_frame(df: pd.DataFrame, schema: TableSchema, *, extra_ok: bool = True) -> None:
    """Validate ``df`` against ``schema``; raise :class:`ContractError` listing all problems."""
    problems: list[str] = []
    for col in schema.columns:
        if col.name not in df.columns:
            problems.append(f"missing column {col.name!r}")
            continue
        s = df[col.name]
        non_null = s.dropna()
        if not col.nullable and len(non_null) != len(s):
            problems.append(f"{col.name!r} has nulls")
        if len(non_null) and not _KIND_CHECKS[col.kind](non_null):
            problems.append(f"{col.name!r} expected {col.kind}, got {s.dtype}")
        if col.allowed is not None:
            bad = set(non_null.unique()) - set(col.allowed)
            if bad:
                problems.append(f"{col.name!r} has disallowed values {sorted(map(str, bad))[:5]}")
    if not extra_ok:
        extra = set(df.columns) - set(schema.column_names)
        if extra:
            problems.append(f"unexpected columns {sorted(extra)}")
    if schema.primary_key and set(schema.primary_key) <= set(df.columns):
        dup = df.duplicated(list(schema.primary_key)).sum()
        if dup:
            problems.append(f"{dup} duplicate rows on primary key {schema.primary_key}")
    if problems:
        raise ContractError(f"{schema.name}: " + "; ".join(problems))


SIDES = ("CT", "T")

MANIFEST = TableSchema(
    "manifest",
    (
        Column("match_id", "str"),
        Column("source", "str"),
        Column("map_name", "str"),
        Column("game_build", "str", nullable=True),
        Column("tick_rate", "float"),
        Column("match_date", "datetime", nullable=True),
        Column("tier", "str", nullable=True),
        Column("tier_source", "str", nullable=True),
    ),
    primary_key=("match_id",),
)

ROUNDS = TableSchema(
    "rounds",
    (
        Column("match_id", "str"),
        Column("round_num", "int"),
        Column("freeze_end_tick", "int"),
        Column("end_tick", "int"),
        Column("winner_side", "str", allowed=SIDES),
        Column("end_reason", "str"),
        Column("is_overtime", "bool"),
    ),
    primary_key=("match_id", "round_num"),
)

STATE_FEATURES = TableSchema(
    "state_features",
    (
        Column("match_id", "str"),
        Column("round_num", "int"),
        Column("tick", "int"),
        Column("round_uid", "str"),
        Column("alive_ct", "int"),
        Column("alive_t", "int"),
        Column("hp_sum_ct", "float"),
        Column("hp_sum_t", "float"),
        Column("bomb_planted", "bool"),
        Column("time_remaining_s", "float"),
        Column("man_advantage", "int"),
        Column("tier", "str", nullable=True),
        Column("map_name", "str"),
    ),
    primary_key=("match_id", "round_num", "tick"),
)

DUELS = TableSchema(
    "duels",
    (
        Column("duel_id", "str"),
        Column("match_id", "str"),
        Column("round_num", "int"),
        Column("tick_start", "int"),
        Column("p1", "str"),
        Column("p2", "str"),
        Column("y_p1_wins", "int", allowed=(0, 1)),
    ),
    primary_key=("duel_id",),
)

EVENT_VALUES = TableSchema(
    "event_values",
    (
        Column("event_id", "str"),
        Column("match_id", "str"),
        Column("round_num", "int"),
        Column("tick", "int"),
        Column("event_type", "str"),
        Column("team_side", "str", allowed=SIDES),
        Column("wp_before", "float"),
        Column("wp_after", "float"),
        Column("wpa", "float"),
    ),
    primary_key=("event_id",),
)

# Columns that must never be used as model features (label leakage). Extend as needed.
LEAKY_COLUMNS: frozenset[str] = frozenset(
    {
        "y_ct_win",
        "winner_side",
        "end_reason",
        "end_tick",
        "round_end_tick",
        "ct_score_after",
        "t_score_after",
        "y_p1_wins",
        "resolved_tick",
        "wp_after",
        "wpa",
    }
)
