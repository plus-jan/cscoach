# 01 — Architecture

## Goal

Post-match analysis of a CS2 match from the PureSkill.gg CSDS corpus. For each player in the match it
produces:
- calibrated round win-probability timelines;
- WPA per action;
- duel quality (xK);
- economy and utility/spatial value;
- at most 3 prioritised, counterfactual coaching points.

Target population: amateur to semi-pro (Valve MM/Premier, FACEIT). Scope of evaluation: the CSDS corpus
(ADR-0003). Output is **per match**, because CSDS has no cross-match player identity (ADR-0005).

## Status: working hypothesis (ADR-0006)

The pipeline below is the **current best hypothesis** of how to get from CSDS data to useful feedback.
It is derived from the literature and has not yet been tested on our data. The decision points in
ROADMAP Part B can change it. Each stage depends on assumptions:

| Stage | Depends on | If they fail |
|---|---|---|
| Tier-aware WP backbone | A-01, A-11, A-12, A-15 | D1: per-tier / no tier / proxy skill |
| WPA as causal credit, counterfactual feedback | A-04, A-05, A-18, A-23 | D2: restricted, or benchmark mode (no "what if") |
| Duels (xK) | A-19, A-20, A-16, A-39 | D3: deprioritise; descriptive duel stats only |
| Economy counterfactuals (gwp, OSE) | A-13, A-21, A-04 | D2/D3: benchmark buy comparisons |
| Spatial (area graph, utility delay) | A-37, A-22 | D3: drop or reduce to `place_name` occupancy |
| Per-player metrics | A-07, A-24, A-25, A-26 | D4: team-level or situation-level feedback |
| The whole module selection | A-41 (planned modules cover where amateurs actually lose rounds) | D3 after exploration E.1–E.4 |

## Pipeline

```
AWS Data Exchange (CSDS daily revisions)
   │  pureskillgg_dsdk: download_adx_dataset_revision / export_*_to_s3
   ▼
local/S3 csds collection (index `csds` + 42 parquet channels per match)
   │  TomeCuratorFs.create_header_tome → dedup → subheader tomes
   │  (platform, rank availability, channel-set version, date window)
   ▼
per-match loading: DsReaderFs/DsReaderS3 + GameDsLoader.get_channels(instructions)
   │  pureskillgg_csgo_dsdk.pop_overtime(max_rounds_csgo=24) where needed
   ▼
derived tables (docs/specs/02): rounds · snapshots · state_features · duels · buys · utility · area_graph
   │  built per match, then assembled across matches as tomes (make_tome)
   ▼
models (docs/specs/03): baseline WP · GBDT WP (tier/platform-conditioned) + calibration · xK · economy
   │
   ▼
valuation: WPA · Shapley credit · xK×WPA decision matrix · counterfactual buys/utility
   │
   ▼
within-match player metrics + shrinkage + reliability gates
   │
   ▼
coaching: detectors → counterfactuals → ranking → narrative (grounded) → JSON report → UI
```

Validation (docs/specs/04) runs on every model and metric. The assumption gate (docs/ASSUMPTIONS.md)
controls what may reach players.

## Components and responsibilities (to be implemented in the code repo)

| Component | Responsibility | Key outputs |
|---|---|---|
| data access | ADX export, header/subheader tomes, dedup, export manifest | tomes, manifest |
| preprocess | round segmentation (phases, warmup, overtime), snapshot sampling | `rounds`, `snapshots` |
| features | leakage-free feature tables from CSDS channels | `state_features`, `duels`, `buys`, `utility_events` |
| spatial | empirical area graph from `place_name` + trajectories, utility delay | `area_graph`, spatial features |
| models | baseline WP, GBDT WP, calibration, xK, model registry + cards | model artefacts |
| economy | rules engine verified on `player_status.money`, buy classes, team sync | `economy_rounds` |
| valuation | WPA, credit assignment, decision matrix | `event_values` |
| validation | splits, metrics, ESS, bootstrap, reliability, gates, reports | reports |
| coaching | shrinkage, detectors, counterfactuals, narratives, assumption gate | `feedback_items` |
| serving | report generation/API/UI (later) | JSON reports |

## Design principles

1. **Single data source:** CSDS through official libraries. A feature that CSDS cannot support is
   out of scope. It is not a reason to add data.
2. **Replaceable models behind one interface** (fit, predict_proba, save/load, model card).
   Challengers are promoted only via the protocol in docs/specs/04 (ADR per promotion).
3. **One WP model is the value function** for WPA, Shapley credit and counterfactual economy/utility.
   Its calibration and counterfactual validity (A-04) bound the accuracy of everything downstream, so
   WP and its verification (MV) come first.
4. **Tier/platform awareness everywhere** (A-01, A-11): conditioning features, stratified evaluation,
   and per-tier calibration where data allows.
5. **Reproducible:** seeds, config hashes, CSDS revision ids, and the channel-set version in every report.
6. **Budget (initial, A-32):** full match analysis < 30 s on 4 cores, excluding download.

## Technology (for the code repo)

Python ≥ 3.11 (dsdk requirement), `pureskillgg-dsdk`, `pureskillgg-csgo-dsdk`, pandas/pyarrow,
scikit-learn, LightGBM (XGBoost acceptable; dsdk has an `xgboost` extra), networkx (area graph), a
statistics stack (scipy/statsmodels). Environment: `uv`, as recommended by PureSkill.
