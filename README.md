# cscoach — CS2 coaching engine

Data-driven, statistically validated coaching for amateur and semi-pro Counter-Strike 2
players: calibrated round **Win Probability**, **WPA** credit, **Expected Kills (xK)**,
economy and spatial analytics, turned into counterfactual, actionable feedback.

- **Start here (humans & Claude Code):** [`CLAUDE.md`](CLAUDE.md)
- **Plan:** [`ROADMAP.md`](ROADMAP.md) · progress in [`docs/PROGRESS.md`](docs/PROGRESS.md)
- **Specs:** [`docs/specs/`](docs/specs) · decisions in [`docs/adr/`](docs/adr)
- **Research basis:** [`docs/research/`](docs/research) (German synthesis + source registry)

## Quickstart

```bash
make install
make check
cscoach synth data/processed/synth.parquet --n-matches 300
cscoach train-wp data/processed/synth.parquet --name synth
cscoach validate models/<run-dir>
```

## Status

Foundation (M0) done: validation core (grouped splits, calibration metrics, ESS, cluster
bootstrap, meta-analytics, gates), synthetic simulator, baseline + GBDT WP with per-tier
calibration. Next: real-demo ingestion (M1). See the roadmap.
