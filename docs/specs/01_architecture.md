# 01 — Architecture

## Goal

Post-match (not live in-game) analysis of a CS2 demo that yields, for each player:
calibrated round win probability timelines, WPA per action, duel quality (xK),
economy decisions, spatial/utility value, and ≤ 3 prioritised, counterfactual coaching
points. Target users: amateur → semi-pro (MM, Premier, FACEIT levels 1–10, low-tier leagues).

## Pipeline

```
.dem ──► ingest (demoparser2) ──► interim parquet (ticks, events, header)
           │                          │
           ▼                          ▼
      manifest (hash, map,     preprocess: rounds, snapshots
      build, tier)                    │
                                      ▼
                    features: state │ duel │ economy │ spatial
                                      │
             ┌────────────────────────┼─────────────────────────┐
             ▼                        ▼                         ▼
      WP model (per tier,       xK model                 economy engine
      calibrated)                                        + nav graph / utility
             │                        │                         │
             └──────────► valuation: WPA, Shapley credit, decision matrix
                                      │
                                      ▼
                   player metrics + shrinkage + meta-analytics gates
                                      │
                                      ▼
                  coaching: detectors → counterfactuals → ranking → narrative
                                      │
                                      ▼
                          JSON report ─► API ─► dashboard
```

## Components & responsibilities

| Package | Responsibility | Key outputs |
|---|---|---|
| `ingest` | Parse `.dem`; load datasets; tier mapping; manifest | `ticks`, `events.*`, `header`, `manifest` |
| `preprocess` | Round segmentation, snapshot sampling | `rounds`, `snapshots` |
| `features` | Leakage-free feature tables | `state_features`, `duels`, `buys` |
| `models` | Baseline WP, GBDT WP, xK, calibration, registry | model artefacts + cards |
| `economy` | Rules engine, buy classes, team sync, counterfactual money | `economy_rounds` |
| `spatial` | Nav graph, area control, utility delay | `spatial_features`, `utility_value` |
| `valuation` | WPA, credit assignment, decision matrix | `event_values`, `player_round_values` |
| `validation` | Everything that proves accuracy | reports, gate verdicts |
| `coaching` | Shrinkage, detectors, counterfactuals, narratives | `feedback_items` |
| `api`/`pipeline` | CLI + service | JSON reports |

## Design principles

1. **Models are replaceable behind interfaces** (`models.base.ProbabilisticModel`):
   `fit`, `predict_proba`, `save`, `load`, `card`. Challenger models must beat the
   champion on the validation protocol to be promoted (ADR per promotion).
2. **One WP model is the value function for everything** (WPA, Shapley, counterfactual
   economy/utility). Its calibration therefore bounds the accuracy of the whole system —
   that is why M3 precedes everything downstream.
3. **Tier awareness everywhere**: models take `tier` as input and are calibrated per tier;
   priors for shrinkage are per tier.
4. **Deterministic & reproducible**: seeds, config hashes, data manifests in every report.
5. **Latency budget** (post-match): full analysis < 30 s per match on 4 cores.

## Technology

Python 3.11 · demoparser2 (Rust core) · polars/pandas/pyarrow · scikit-learn · LightGBM ·
networkx (nav graph) · FastAPI · pytest/ruff/mypy. Optional: PyTorch for sequence
challengers (M3.6), `awpy` for map/nav data (M7.1, pending ADR).
