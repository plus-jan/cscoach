"""Evaluation reports and acceptance gates (configs/validation.yaml)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cscoach.config import REPO_ROOT, config_hash, load_config
from cscoach.validation.bootstrap import cluster_bootstrap
from cscoach.validation.ess import effective_sample_size
from cscoach.validation.metrics import (
    brier_score,
    brier_skill_score,
    expected_calibration_error,
    score_all,
)


@dataclass
class GateResult:
    name: str
    passed: bool
    value: float
    threshold: float
    detail: str = ""


@dataclass
class EvaluationReport:
    model: str
    overall: dict[str, Any]
    strata: dict[str, dict[str, dict[str, float]]]
    gates: list[GateResult] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "passed": self.passed,
            "overall": self.overall,
            "strata": self.strata,
            "gates": [g.__dict__ for g in self.gates],
            "meta": self.meta,
        }

    def write(self, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "metrics.json"
        path.write_text(json.dumps(self.to_dict(), indent=2, default=_json_default))
        return path


def _json_default(o: object) -> object:
    if isinstance(o, np.integer | np.floating):
        return o.item()
    if isinstance(o, np.bool_):
        return bool(o)
    return str(o)


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def evaluate_probabilistic(
    df: pd.DataFrame,
    *,
    model: str,
    y_col: str,
    p_col: str,
    group_col: str = "match_id",
    cluster_col: str | None = "round_uid",
    baseline_col: str | None = None,
    strata_cols: tuple[str, ...] = ("tier", "map_name"),
    validation_cfg: dict[str, Any] | None = None,
) -> EvaluationReport:
    """Evaluate predictions in ``df`` (test fold only!) and apply gates for ``model``.

    ``model`` selects the gate block (``wp`` or ``xk``) in ``configs/validation.yaml``.
    """
    cfg = validation_cfg or load_config("validation")
    bcfg, ecfg = cfg["bootstrap"], cfg["ece"]
    y = df[y_col].to_numpy(float)
    p = df[p_col].to_numpy(float)
    groups = df[group_col].to_numpy()

    def ece(y_: np.ndarray, p_: np.ndarray) -> float:
        return expected_calibration_error(y_, p_, ecfg["n_bins"], ecfg["strategy"])

    boot = {"n_resamples": bcfg["n_resamples"], "alpha": bcfg["alpha"], "seed": bcfg["seed"]}
    overall: dict[str, Any] = score_all(y, p, ecfg["n_bins"])
    overall["n_groups"] = int(pd.Series(groups).nunique())
    overall["brier_ci"] = cluster_bootstrap(brier_score, (y, p), groups, **boot).as_dict()
    overall["ece_ci"] = cluster_bootstrap(ece, (y, p), groups, **boot).as_dict()
    if cluster_col and cluster_col in df:
        overall["ess_residual"] = effective_sample_size(y - p, df[cluster_col].to_numpy())
    bss_ci = None
    if baseline_col:
        pb = df[baseline_col].to_numpy(float)
        bss_ci = cluster_bootstrap(brier_skill_score, (y, p, pb), groups, **boot)
        overall["brier_skill_vs_baseline"] = bss_ci.as_dict()

    strata: dict[str, dict[str, dict[str, float]]] = {}
    for col in strata_cols:
        if col not in df:
            continue
        strata[col] = {}
        for val, part in df.groupby(col, dropna=False):
            if part[y_col].nunique() < 2:
                continue
            s = score_all(part[y_col], part[p_col], ecfg["n_bins"])
            s["n_groups"] = float(part[group_col].nunique())
            if cluster_col and cluster_col in part:
                s["n_clusters"] = float(part[cluster_col].nunique())
            strata[col][str(val)] = s

    gates = _apply_gates(model, overall, strata, bss_ci.low if bss_ci else None, cfg)
    meta = {
        "created_utc": datetime.now(UTC).isoformat(),
        "git_sha": git_sha(),
        "validation_config_hash": config_hash(cfg),
    }
    return EvaluationReport(model, overall, strata, gates, meta)


def _apply_gates(
    model: str,
    overall: dict[str, Any],
    strata: dict[str, dict[str, dict[str, float]]],
    bss_low: float | None,
    cfg: dict[str, Any],
) -> list[GateResult]:
    g = cfg["gates"][model]
    out = [GateResult("ece_overall", overall["ece"] <= g["ece_max"], overall["ece"], g["ece_max"])]
    min_n = g.get("min_rounds_per_stratum", g.get("min_duels_per_stratum", 0))
    count_key = "n_clusters" if model == "wp" else "n"
    for col, key in (("tier", "ece_max_per_tier"), ("map_name", "ece_max_per_map")):
        if key not in g or col not in strata:
            continue
        for val, s in strata[col].items():
            if s.get(count_key, s["n"]) < min_n:
                continue
            out.append(GateResult(f"ece_{col}={val}", s["ece"] <= g[key], s["ece"], g[key]))
    if "auc_min" in g:
        out.append(GateResult("auc", overall["auc"] >= g["auc_min"], overall["auc"], g["auc_min"]))
    if "brier_skill_vs_baseline_min" in g:
        thr = g["brier_skill_vs_baseline_min"]
        if bss_low is None:
            out.append(GateResult("bss_vs_baseline", False, float("nan"), thr, "no baseline"))
        else:
            out.append(GateResult("bss_vs_baseline_ci_low", bss_low > thr, bss_low, thr))
    return out
