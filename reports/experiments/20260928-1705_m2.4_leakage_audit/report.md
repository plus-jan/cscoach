# M2.4 — Leakage audit

Data provided by PureSkill.gg. Derived data, CC BY-NC-SA 4.0 (ADR-0008).

## Reproduce
code commit `652c7f7` · config `configs/leakage_audit.yaml` · `uv run python -m cscoach.verify.leakage_audit --report-dir <dir>`.
Input: state features (M2.3, with `decided_tick` from MV.1) of 300 clean seeded matches (pre-top-up); label
`y_ct_win` from `rounds.winner_side`, attached only in the audit table.

## Method
Per numeric feature, the orientation-free AUC (max(A, 1 − A), Mann–Whitney with ties) against the round winner at
the freeze-end snapshot (`second_in_round` = 0); 95 % cluster-bootstrap CIs over matches (500 resamples, A-10).
Gate: no feature above 0.99 (A-46). Unit tests: a planted label copy is flagged; honest weak signal is not.
Supplementary: the best single-feature AUC per time bin across all snapshots.

## Result
**Gate passes.** 6,215 freeze-end snapshots, 300 matches. Top AUCs: ct_equip_value 0.630 [0.615, 0.644],
ct_molotovs 0.613 [0.598, 0.627], ct_primaries 0.611 [0.597, 0.625], ct_hes 0.609, ct_flashes 0.609, ct_smokes 0.609,
ct_kits 0.608, ct_armor_sum 0.601. All features and CIs: `summary.json`.

Profile (best single feature per `second_in_round` bin): 0–1 s ct_equip_value 0.633; 1–10 s 0.636; 10–20 s
man_advantage 0.655; 20–40 s 0.807; 40–60 s 0.871; 60–80 s 0.874; 80–100 s 0.869; 100–130 s 0.853. Nothing
approaches 1 at any time; late-round predictiveness comes from man advantage, as expected.

## Note
Before MV.1's `decided_tick`, v30 snapshots included ~6.7 s after the decision (F-07); this audit runs on the
corrected tables. Re-run on the refreshed full data after the M1.5 top-up (with M2.3).
