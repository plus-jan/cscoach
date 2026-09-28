"""Command-line interface: ``cscoach --help``."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import typer

from cscoach.config import REPO_ROOT, config_hash, load_config

app = typer.Typer(help="CS2 coaching engine", no_args_is_help=True)


@app.command()
def parse(demo: Path, out: Path = REPO_ROOT / "data/interim") -> None:
    """Parse a .dem file into interim parquet tables."""
    from cscoach.ingest.demo_parser import parse_demo

    parsed = parse_demo(demo)
    typer.echo(f"wrote {parsed.write(out)}")


@app.command()
def synth(out: Path, n_matches: int = 200, seed: int = 0) -> None:
    """Write a synthetic snapshot table (for pipeline development)."""
    from cscoach.synthetic import simulate_matches

    df = simulate_matches(n_matches=n_matches, seed=seed)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out)
    typer.echo(f"wrote {len(df)} rows to {out}")


@app.command()
def train_wp(data: Path, name: str = "wp", config: str = "model_wp") -> None:
    """Train baseline + GBDT WP on a state-feature table; save model + test predictions."""
    from cscoach.models.training import train_wp as _train

    cfg = load_config(config)
    df = pd.read_parquet(data)
    res = _train(df, cfg)
    run = REPO_ROOT / "models" / f"{datetime.now(UTC):%Y%m%dT%H%M%S}_{name}"
    res.model.save(run)
    res.test_frame.to_parquet(run / "test_predictions.parquet")
    (run / "train_meta.json").write_text(
        json.dumps({"config_hash": config_hash(cfg), "data": str(data)}, indent=2)
    )
    typer.echo(str(run))


@app.command()
def validate(run: Path, model: str = "wp") -> None:
    """Evaluate test predictions of a run against configs/validation.yaml gates."""
    from cscoach.validation.report import evaluate_probabilistic

    if model != "wp":
        raise typer.BadParameter("only wp is implemented (xk: M4.3)")
    df = pd.read_parquet(run / "test_predictions.parquet")
    rep = evaluate_probabilistic(
        df, model="wp", y_col="y_ct_win", p_col="p_wp", baseline_col="p_baseline"
    )
    path = rep.write(REPO_ROOT / "reports/experiments" / f"{run.name}_validate")
    for g in rep.gates:
        typer.echo(f"{'PASS' if g.passed else 'FAIL'}  {g.name}: {g.value:.4f} (thr {g.threshold})")
    typer.echo(f"report: {path}")
    raise typer.Exit(0 if rep.passed else 1)


@app.command()
def analyze(demo: Path) -> None:
    """Full post-match analysis → JSON coaching report (M10.1)."""
    raise NotImplementedError("M10.1: end-to-end analysis pipeline")


if __name__ == "__main__":
    app()
