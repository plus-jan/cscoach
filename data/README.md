# Data

Git-ignored. Layout:

- `raw/<source>/*.dem` — original demos (never modified)
- `interim/<match_id>/` — parsed parquet per table (`ticks.parquet`, `kills.parquet`, ...)
- `processed/` — modelling tables (`state_features.parquet`, `duels.parquet`, ...)
- `external/` — third-party datasets (PureSkill, map/nav data)
- `manifest.parquet` — one row per match (see docs/specs/02_data_contracts.md)

## Sources (to be documented by M1.x)

| Source | Tier coverage | How to obtain | License/ToS notes |
|---|---|---|---|
| PureSkill.gg CS2 dataset | amateur/MM, rank-labelled | Kaggle / AWS Data Exchange | check dataset license |
| User-uploaded demos | any | MM "download replay", FACEIT match page | user consent |
| FACEIT API | levels 1–10 | Data API key (env `FACEIT_API_KEY`) | FACEIT API ToS |
| HLTV pro demos | pro (reference / transfer study) | manual download | HLTV ToS; no scraping at scale |

Never commit demos or personal data. Steam IDs are personal data: pseudonymise in
reports shared outside the project.
