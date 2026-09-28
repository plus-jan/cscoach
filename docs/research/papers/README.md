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
6. **Adding a paper:** follow the `add-paper` skill (`.claude/skills/add-paper/SKILL.md`).
7. **Data policy:** papers inform methods only. Features and evaluations use the CSDS corpus exclusively
   (ADR-0003), even when a paper used other data.

## Index

| id | Paper | Game / data | Questions | Used in |
|---|---|---|---|---|
| [same_player_verification_cs2](same_player_verification_cs2.md) | Account Consistency from Gameplay Traces: Same-Player Verification in CS2 (Zhang 2026, **v2**) | CS2 amateur + pro | A, C, E | M4.2 xK features, A-20, A-29, ADR-0005 ethics |
| [learning_to_move_like_pros](learning_to_move_like_pros.md) | Learning to Move Like Professional CS Players (Durst et al. 2024) | CS:GO pro, dust2 | G, I | CSDS quality caveat (A-16/A-40), M9.1 region detectors, MV.12/13 |
| [x_ego_cs](x_ego_cs.md) | X-Ego (Wang, Hans, Ustun 2025) | CS2 pro video, Mirage | G, J | named-area positions (A-37); data out of scope |
| [valorant_round_outcome_tactical](valorant_round_outcome_tactical.md) | Round Outcome Prediction in VALORANT (Hayakawa et al. 2025) | VALORANT | B, G | M7.2 event features (weak evidence) |
| [champ_matchmaking](champ_matchmaking.md) | CHAMP cross-domain matchmaking (Wang et al. 2026) | MOBA | B, C | ADR-0002 tier conditioning, per-tier reporting |
| [pandaskill](pandaskill.md) | PandaSkill (De Bois et al. 2025) | LoL pro | D | M8, monotone GBDT, ECE |
| [tar2_credit_assignment](tar2_credit_assignment.md) | TAR² temporal-agent reward redistribution (Kapoor et al. 2025) | MARL sims | D | M5.3/MV.11: WPA telescoping test; negative credit needed |
| [contextual_xt_spatial](contextual_xt_spatial.md) | Contextual Expected Threat (Everett et al. 2022) | football | D, G | M7.2/M7.4: judge spatial features on outcome |
| [xenopoulos_valuing_actions_csgo](xenopoulos_valuing_actions_csgo.md) | Valuing Player Actions in CS:GO (Xenopoulos et al. 2020) | CS:GO pro | A, D, H | WP/WPA reference design, M3.1 benchmark, M5.2, A-01 |
| [xenopoulos_optimal_economy](xenopoulos_optimal_economy.md) | Optimal Team Economic Decisions in CS (Xenopoulos et al. 2021) | CS:GO pro | F | game-level WP, OSE (M6.3), buy types (A-21) |
| [franks_meta_analytics](franks_meta_analytics.md) | Meta-Analytics (Franks et al. 2016) | NBA/NHL | H | player-metric D/S/I (specs/04 §4), MV.9, A-25 |
| [brill_yurko_wp_difficulty](brill_yurko_wp_difficulty.md) | Exploring the Difficulty of Estimating WP (Brill, Yurko, Wyner 2025) | simulation | H | two uncertainty kinds, fractional bootstrap (MV.4, A-24) |
| [gig_economy_esports_coaching](gig_economy_esports_coaching.md) | Understanding Game Coaching on Gig Platforms (Lee & Savage 2026) | interviews | C, I | specs/05, M9, M10.3 |

All listed papers are full-text verified (`verified: true` in `../sources.yaml`).

**Still missing (full text needed, see `../sources.yaml` for URLs):** **xenopoulos_pro_vs_amateur_wp**
(highest priority: direct test of A-01; it used earlier PureSkill data), play_like_champions,
dynamic_xt, hltv_rating_3 (HLTV article, save as PDF).

## By research question

- **A. WP in Counter-Strike:** xenopoulos_valuing_actions_csgo, same_player_verification_cs2 (features only); *missing:* xenopoulos_pro_vs_amateur_wp
- **B. WP in other games:** valorant_round_outcome_tactical, champ_matchmaking
- **C. Skill tiers:** champ_matchmaking (conditioning lesson), same_player_verification_cs2 (domain-matched training matters, Table 9), xenopoulos_optimal_economy (pooled model + conditioning feature beat per-group models)
- **D. Action valuation / credit:** xenopoulos_valuing_actions_csgo, pandaskill, tar2_credit_assignment, contextual_xt_spatial; *missing:* hltv_rating_3, dynamic_xt
- **E. Duels (xK):** same_player_verification_cs2 (mechanics features)
- **F. Economy:** xenopoulos_optimal_economy; *missing:* hltv_rating_3
- **G. Spatial:** learning_to_move_like_pros, x_ego_cs, contextual_xt_spatial, valorant_round_outcome_tactical; *missing:* dynamic_xt
- **H. Statistical validity:** franks_meta_analytics, brill_yurko_wp_difficulty, xenopoulos_valuing_actions_csgo (meta-metrics applied), pandaskill (ECE), same_player_verification_cs2 (cluster bootstrap CIs)
- **I. Coaching:** gig_economy_esports_coaching, learning_to_move_like_pros (region-based mistake metrics); *missing:* play_like_champions

## Cross-paper takeaways (so far)

1. **Calibration is rarely reported.** Only PandaSkill reports ECE. VALORANT and CHAMP report accuracy
   (CHAMP adds RMSE), and xT reports log-likelihood without CIs. Our gates in `docs/specs/06_parameters.md`
   go beyond the literature; don't relax them to match the papers.
2. **Skill/domain groups need explicit conditioning or matched training.** Naive pooling can do worse
   than a single-group model [champ_matchmaking]. Mixing amateur and pro data reduced pro performance
   [same_player_verification_cs2, Table 9]. This supports ADR-0002 while MV.3 is open.
3. **Low-level mechanics carry strong player-specific signal** that outcome stats miss (AUC 0.572 → 0.855,
   v2) [same_player_verification_cs2]. This is the basis for the execution side of xK.
   **Ethics:** the same signal can re-identify players, which the CSDS DSA forbids (ADR-0005).
4. **Tree models on engineered features are the practical default** at this data scale [pandaskill,
   same_player_verification_cs2].
5. **Gains on intermediate targets don't guarantee gains on the outcome:** xT transitions improved 19.2%,
   but goal probability only ~0.4% [contextual_xt_spatial]. Judge every feature on WP log-loss with CIs.
6. **Positions are best described as named areas:** callout regions for mistakes, teamwork and
   location prediction [learning_to_move_like_pros, x_ego_cs]. This is the basis for our `place_name`
   area graph (A-37).
7. **WP is a potential function:** WPA telescopes over a round, the property that credit-redistribution
   theory relies on [tar2_credit_assignment]. Our credit must also allow negative values.
8. **Most evaluations leak or under-report uncertainty:** splits by round or by person rather than by
   match, and 100-round test sets. Treat reported numbers as optimistic.
9. **WP intervals are wider than they look:** refit bootstraps under-cover (the cluster bootstrap reaches
   0.71 at nominal 0.90). A tuned fractional bootstrap is needed, and tuning it needs a simulator with
   known truth [brill_yurko_wp_difficulty]. Keep all snapshots; they help despite being correlated.
10. **Player metrics need the real Franks definitions:** discrimination vs sampling noise, stability
    across periods, and independence in latent space. Shrinkage improves both D and S
    [franks_meta_analytics].
11. **The CS-specific prior art already exists:** WPA from damage events with victim-negative credit,
    and game-level WP for buy decisions (OSE). Both authors flag skill heterogeneity and confounding as
    open issues [xenopoulos_valuing_actions_csgo, xenopoulos_optimal_economy], which are our A-01 and
    A-04.
12. **CSDS data quality:** an independent group notes that PureSkill.gg data has no guarantee on capture
   frequency and may drop data [learning_to_move_like_pros]. Measure it before building sub-second
   features (MV.1).

Licenses: see each file's front matter. Only the coaching paper is confirmed CC BY. Keep this repository
private unless redistribution rights are confirmed for the others.
