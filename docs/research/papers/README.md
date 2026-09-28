# Research papers (full text for agents)

Full-text markdown of the papers behind the design, each with a hand-written
**cscoach notes** block at the top: verified numbers, corrections to the original
synthesis, and where the paper is used in this project.

## How agents should use this folder

1. **Before designing or changing a model, feature, metric or feedback format**, look up the
   relevant research question below and read the *cscoach notes* block of each listed paper
   (the block is short; read the full text only when you need details or formulas).
2. **Cite by id** (`sources.yaml` id) in specs, ADRs and docstrings, e.g. `[pandaskill]`.
3. **Trust order:** paper full text > cscoach notes > `sources.yaml` > `research_synthesis_de.md`.
   The German synthesis contains known errors (see *Corrections* in each note).
4. Only cite claims from entries with `verified: true` as design justification. `search` means only
   the paper's existence was confirmed.
5. **Numbers:** tables and equations may be garbled by PDF conversion. Check the PDF before quoting a
   number in a spec, and never quote a number from these papers in player-facing text.
6. **Adding a paper:** add an entry to `../sources.yaml` (with `arxiv:` if applicable), then run
   `python scripts/pdf_to_md.py <file.pdf>`. Then fill in the notes block, set `local:` and `verified:`,
   and add a row below. Re-running the script keeps the notes block.

## Index

| id | Paper | Game | Verified | Questions | Used in |
|---|---|---|---|---|---|
| [same_player_verification_cs2](same_player_verification_cs2.md) | Same-Player Verification for Account Consistency in CS2 (Zhang 2026) | CS2 | ✅ | A, C | M4.2 duel features, M3.5, player habits |
| [valorant_round_outcome_tactical](valorant_round_outcome_tactical.md) | Round Outcome Prediction in VALORANT (Hayakawa et al. 2025) | VALORANT | ✅ | B, G | M7.2 event features (weak evidence) |
| [champ_matchmaking](champ_matchmaking.md) | CHAMP cross-domain matchmaking (Wang et al. 2026) | MOBA | ✅ | B, C | ADR-0002 tier conditioning, per-tier reporting |
| [gig_economy_esports_coaching](gig_economy_esports_coaching.md) | Understanding Game Coaching on Gig Platforms (Lee & Savage 2026) | many | ✅ | C, I | specs/05 feedback design, M9, M10.3 |
| [pandaskill](pandaskill.md) | PandaSkill (De Bois et al. 2025) | LoL | ✅ | D | M8 player ratings, monotone GBDT, ECE |

**Still missing (full text needed, see `../sources.yaml` for URLs):** franks_meta_analytics,
brill_yurko_wp_difficulty, xenopoulos_valuing_actions_csgo, xenopoulos_optimal_economy,
learning_to_move_like_pros, x_ego_cs, tar2_credit_assignment, play_like_champions,
contextual_xt_spatial, dynamic_xt, hltv_rating_3.

## By research question

- **A. WP in Counter-Strike:** same_player_verification_cs2 (features only); *missing:* xenopoulos_valuing_actions_csgo
- **B. WP in other games:** valorant_round_outcome_tactical, champ_matchmaking
- **C. Skill tiers:** champ_matchmaking (conditioning lesson), same_player_verification_cs2 (pro data doesn't transfer to amateurs)
- **D. Action valuation / credit:** pandaskill; *missing:* hltv_rating_3, tar2_credit_assignment, contextual_xt_spatial, dynamic_xt
- **E. Duels (xK):** same_player_verification_cs2 (mechanics features)
- **F. Economy:** *missing:* xenopoulos_optimal_economy, hltv_rating_3
- **G. Spatial:** valorant_round_outcome_tactical; *missing:* learning_to_move_like_pros, x_ego_cs, dynamic_xt
- **H. Statistical validity:** pandaskill (ECE practice); *missing:* franks_meta_analytics, brill_yurko_wp_difficulty
- **I. Coaching:** gig_economy_esports_coaching; *missing:* play_like_champions

## Cross-paper takeaways (so far)

1. **Calibration is rarely reported.** VALORANT and CHAMP report accuracy (CHAMP also RMSE); only
   PandaSkill reports ECE. Our gates in `configs/validation.yaml` go beyond the literature. Don't relax them
   to match the papers.
2. **Pooling across skill groups needs explicit conditioning.** Without it, performance can fall below a
   single-group model. Pro data did not help an amateur CS2 model [champ_matchmaking,
   same_player_verification_cs2]. This supports ADR-0002.
3. **Low-level mechanics carry strong player-specific signal** (crosshair control, counter-strafe timing,
   firing rhythm) that outcome stats miss (AUC 0.599 vs 0.831) [same_player_verification_cs2]. This is the
   basis for the execution side of xK.
4. **Monotone GBDTs are the practical default** at esports data scale [pandaskill,
   same_player_verification_cs2].
5. **Coaching value comes from individual, recurring-pattern diagnosis with visible evidence**, not
   generic tips [gig_economy_esports_coaching].
6. **Most evaluations leak or under-report uncertainty:** random or person-disjoint splits that are not
   match-disjoint, and 100-round test sets. Treat reported numbers as optimistic.

Licenses: see each file's front matter. Only the coaching paper is confirmed CC BY. Keep this repository
private unless redistribution rights are confirmed for the others.
