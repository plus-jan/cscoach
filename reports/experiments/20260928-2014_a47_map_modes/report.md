# A-47 — WP on bomb-defusal maps only

- commit: 5b3cd71 · script: `check.py` (this folder) · config: `configs/wp_split.yaml` · data: the eligible WP matches
  of the 2026-09-28 refresh (header tome `header.2025-09-01,2026-09-28.full`). Data provided by PureSkill.gg.
- 10,036 eligible matches: 9,931 on `de_` maps, 105 on `cs_` hostage maps (cs_office 85, cs_italy 8, cs_shelter 7,
  cs_agency 3, cs_alpine 2); 2,143 cs_ rounds.
- cs_ rounds end only with win reasons 8/9 (elimination) and 11/13 (hostages rescued / not rescued); de_ rounds
  never have 11/13 (`win_reason_by_map_kind.csv`).
- bomb-planted snapshots: de_ 3,066,732 of 21,519,341; cs_ 0 of 207,516.
- Verdict: A-47 supported; `wp.map_prefixes: [de_]`. The sealed split `wp_v1` predates the rule and still lists the
  105 matches (train 54, calibration 7, test 21, temporal 23); they are absent from `wp_table_v1`, so no fold sees them.
