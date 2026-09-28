# M3.6 — v30 decided-tick fix (F-15), rebuild, WP v2: sealed look 2 (declared new experiment)

- fix: commit 22323e0 — `cscoach.data.rounds.decided_ticks`: a T elimination after the plant is no deciding event
  (test `test_decided_tick_v30_t_elimination_after_plant_does_not_decide`). Rebuild (refresh 20260928-2230, commit
  22323e0): rounds 13,484 matches, snapshots 10,036, features 10,038 (21,968,575 rows, was 21,732,387). 23,559 v30
  rounds (10.7% of v30) now end later (all CT wins; median +10.1 s, p90 +14.8 s); no v42 round and no winner changed.
- leakage audit re-run (`reports/experiments/20260928-2258_m2.4_leakage_audit_refresh/`): max freeze-end AUC 0.626
  (ct_equip_value), gate passes.
- bias re-check on training matches (`diag_after_fix/`, same script as M3.4): v30 defuse rounds after a T wipe now
  have T-wiped snapshots 155/155 (was 0/155); CT win at the first T-wiped post-plant snapshot now agrees between
  channel sets (kit, 10–20 s left: v30 0.98 of 2,187 rounds, v42 0.98 of 252; was 0.02 of 42).
- refit `models/wp_v2` (`reports/experiments/20260928-2302_m3.6_wp_v2_fit/`, commit a4e1fe7; unchanged M3.2/M3.3
  configs): GBDT 735 trees on 6,293 training matches (13,792,533 rows); global Platt a 0.963, b 0.009 on 897
  calibration matches.
- evaluation: commit a4e1fe7, pre-registered `configs/wp_validate.yaml`; `sealed_looks.json`: **look 2**, new
  experiment (look 1 = wp_v1, M3.4). The test rows differ from look 1 (restored snapshots), so v1 and v2 log-losses
  are not directly comparable. Data provided by PureSkill.gg.

| fold | model | log-loss | Brier | ECE | MCE | AUC |
|---|---|---|---|---|---|---|
| test (1,804 m, 3,972,940 rows) | **wp_v2** | 0.4821 [0.4783, 0.4860] | 0.1620 | 0.0044 [0.0034, 0.0073] | 0.010 | 0.841 |
| test | baseline_wp | 0.5145 [0.5109, 0.5181] | 0.1744 | 0.0090 | 0.033 | 0.813 |
| temporal (937 m, 2,017,070 rows) | **wp_v2** | 0.4788 [0.4736, 0.4844] | 0.1606 | 0.0026 [0.0035, 0.0075]* | 0.006 | 0.844 |
| temporal | baseline_wp | 0.5115 [0.5068, 0.5164] | 0.1731 | 0.0076 | 0.031 | 0.816 |

\* The resampled ECE is biased upward (A-07 note), so the CI can sit above the point estimate.
Δlog-loss vs baseline: test 0.0323 [0.0304, 0.0341], temporal 0.0327 [0.0303, 0.0351]; BSS 0.071 [0.067, 0.075] /
0.072 [0.067, 0.078].

Gates (A-06/A-07): all pass on both folds — ECE 0.0044 / 0.0026; worst tier 0.012 (high) / 0.019 (high); worst gated
map 0.032 / 0.022; BSS CI low 0.067 / 0.067. Skipped as < 500 rounds: test maps de_golden, de_grail, de_warden;
temporal semipro (22 matches, ECE 0.027) and maps de_fachwerk, de_overpass, de_train, de_vertigo.

Alive states (the F-15 bias): 1v0 ECE test 0.012 (v1 0.047), temporal 0.020 (v1 0.247); 2v0 0.009 / 0.008 (v1
0.044 / 0.100); 3v0 0.004 / 0.006. v42 ECE on test 0.0095 (v1 0.0113).
