# CSDS code decoding and game rules (MV.1)

Derived empirically from 400 clean seeded matches (200 v30, 200 v42; 2025-09 … 2026-09; builds 10521–10924),
report `reports/experiments/*_mv1_decoding/`. Data provided by PureSkill.gg. Assumptions: A-13, A-14, A-15, A-16, A-39.

## Sides and teams
| field | value | meaning | evidence |
|---|---|---|---|
| `team_code`, `player_team_code`, `winner_team_code` | 2 | T | `win_reason_message` agrees in every row; `player_info` sides swap at 13 |
| | 3 | CT | |
| side swaps | rounds 13, 28, 34, 40 | first overtime half keeps the second-half sides | `player_info` (M2.1) |

v30 parser: `winner_team_code` is stale in the first round of every half (fixed in `cscoach.data.rounds`, F-05).

## Round end
`win_reason_code` (v42 only; v30 carries only 8/9 = winner side):

| code | message | winner | meaning |
|---|---|---|---|
| 1 | #SFUI_Notice_Target_Bombed | T | bomb exploded |
| 7 | #SFUI_Notice_Bomb_Defused | CT | bomb defused |
| 8 | #SFUI_Notice_CTs_Win | CT | T eliminated |
| 9 | #SFUI_Notice_Terrorists_Win | T | CT eliminated (75 % after a plant) |
| 11 | #SFUI_Notice_All_Hostages_Rescued | CT | hostage maps |
| 12 | #SFUI_Notice_Target_Saved | CT | round time ran out (exactly 115.0 s after freeze end) |
| 13 | #SFUI_Notice_Hostages_Not_Rescued | T | hostage maps, time |
| 17 | #SFUI_Notice_Terrorists_Surrender | CT | surrender vote |

For v30, derive the reason from events: explosion / defuse (`bomb_state`), elimination (`player_death` of the whole
losing side), else time.

**Round-end tick:** v42 `round_end.tick` is the deciding tick (explosion/defuse gap 0 ticks; `round_officially_ended`
448 or 544 ticks later). v30 `round_end.tick` is 19–20 ticks before `round_officially_ended`, i.e. **~6.7 s after the
decision** → use `rounds.decided_tick` = min(end − 429 ticks, deciding event).

## Bomb sites
`site_code` is **not** a stable site id: it is a per-server entity index (e.g. de_train 100 = B in v30, A in v42). Use
the planter's `player_status.place_name` at the plant tick: `BombsiteA` / `BombsiteB` (3,961 of 3,962 plants).

## Hit boxes (`player_hurt.hit_box_code`, Source hit groups)
| code | hit group | evidence |
|---|---|---|
| 0 | generic (grenades, fire, falls) | no body-part damage pattern |
| 1 | head | AK-47 mean damage 108.4 (≈ 4×); 12,462 of 12,465 v42 killing hits are `is_headshot` |
| 2 | chest | AK-47 26.0 |
| 3 | stomach | AK-47 32.6 (1.25×) |
| 4 / 5 | left / right arm | 25.9 / 25.8 |
| 6 / 7 | left / right leg | 23.8 / 24.0 |
| 8 | neck | 25.9 |

v30 has garbage values (large or negative integers) in 1.2 % of hits → treat codes outside 0–8 as unknown.

## Weapons (`*_weapon_code` = Valve item definition index; identical in v30 and v42)
`attacker_weapon_code` is the weapon **held** at the event (as-of merged); `weapon_name` is the damage source, so a
grenade kill can carry the code of the held rifle. Purity = share of the top `weapon_name` per code.

| code | weapon_name | class | n | purity |
|---|---|---|---|---|
| 1 | deagle | pistol | 28150 | 0.98 |
| 2 | elite | pistol | 7821 | 0.99 |
| 3 | fiveseven | pistol | 8979 | 0.98 |
| 4 | glock | pistol | 71408 | 0.99 |
| 7 | ak47 | rifle | 411329 | 0.98 |
| 8 | aug | rifle | 6167 | 0.99 |
| 9 | awp | sniper | 33300 | 0.93 |
| 10 | famas | rifle | 27275 | 0.98 |
| 11 | g3sg1 | sniper | 669 | 1.00 |
| 13 | galilar | rifle | 59916 | 0.99 |
| 14 | m249 | heavy | 1434 | 0.98 |
| 16 | m4a1 | rifle | 95336 | 0.98 |
| 17 | mac10 | smg | 53234 | 0.99 |
| 19 | p90 | smg | 25429 | 0.99 |
| 23 | mp5sd | smg | 10620 | 0.82 |
| 24 | ump45 | smg | 3435 | 0.99 |
| 25 | xm1014 | heavy | 10868 | 0.97 |
| 26 | bizon | smg | 6971 | 0.99 |
| 27 | mag7 | heavy | 2711 | 0.97 |
| 28 | negev | heavy | 26374 | 1.00 |
| 29 | sawedoff | heavy | 458 | 0.98 |
| 30 | tec9 | pistol | 13819 | 0.99 |
| 31 | taser | equipment | 187 | 0.95 |
| 32 | hkp2000 | pistol | 5386 | 0.98 |
| 33 | mp7 | smg | 37821 | 0.99 |
| 34 | mp9 | smg | 49644 | 0.98 |
| 35 | nova | heavy | 2756 | 0.96 |
| 36 | p250 | pistol | 8951 | 0.98 |
| 38 | scar20 | sniper | 1234 | 0.98 |
| 39 | sg556 | rifle | 6300 | 0.99 |
| 40 | ssg08 | sniper | 12509 | 0.97 |
| 42 | knife | knife | 34240 | 0.97 |
| 43 | flashbang | grenade | 26949 | 0.96 |
| 44 | hegrenade | grenade | 23881 | 0.94 |
| 45 | smokegrenade | grenade | 25808 | 0.97 |
| 46 | molotov | grenade | 7970 | 0.97 |
| 47 | decoy | grenade | 1143 | 0.99 |
| 48 | incgrenade | grenade | 11722 | 0.95 |
| 49 | inferno | grenade | 134 | 0.58 |
| 59 | knife_t | knife | 25748 | 0.96 |
| 60 | m4a1_silencer | rifle | 195779 | 0.81 |
| 61 | usp_silencer | pistol | 66060 | 0.82 |
| 63 | cz75a | pistol | 642 | 0.99 |
| 64 | revolver | pistol | 2218 | 0.83 |
| 500 | bayonet | knife | 1796 | 0.96 |
| 503 | knife_css | knife | 360 | 0.98 |
| 505 | knife_flip | knife | 1788 | 0.98 |
| 506 | knife_gut | knife | 969 | 0.95 |
| 507 | knife_karambit | knife | 1888 | 0.97 |
| 508 | knife_m9_bayonet | knife | 998 | 0.96 |
| 509 | knife_tactical | knife | 2136 | 0.97 |
| 512 | knife_falchion | knife | 2521 | 0.97 |
| 514 | knife_survival_bowie | knife | 2249 | 0.97 |
| 515 | knife_butterfly | knife | 2790 | 0.95 |
| 516 | knife_push | knife | 2781 | 0.97 |
| 517 | knife_cord | knife | 1448 | 0.98 |
| 518 | knife_canis | knife | 1530 | 0.94 |
| 519 | knife_ursus | knife | 625 | 0.92 |
| 520 | knife_gypsy_jackknife | knife | 941 | 0.97 |
| 521 | knife_outdoor | knife | 727 | 0.96 |
| 522 | knife_stiletto | knife | 1108 | 0.97 |
| 523 | knife_widowmaker | knife | 2008 | 0.96 |
| 525 | knife_skeleton | knife | 1366 | 0.97 |
| 526 | knife_kukri | knife | 1842 | 0.96 |

## Timers (A-14)
| timer | measured | note |
|---|---|---|
| round time | 115.0 s from freeze end (v42 time-outs; v30 after the end-tick correction) | |
| bomb | **41.0 s** from `bomb_planted` to `bomb_exploded` (all 585 explosions) | parameter set to 41 |
| freeze | **15 s or 20 s per match** (124 of 400 matches 15 s, the rest 20 s; rounds 1 and 13 longer) | tactical pauses extend it |

## Economy (A-13; one rule set for the whole window — no change between builds 10521 and 10924)
| rule | value |
|---|---|
| start money / half start / overtime-block start | 800 / 800 / **10,000** |
| win: elimination or time / bomb exploded or defused | 3,250 / 3,500 |
| loss ladder | 1,400, 1,900, 2,400, 2,900, 3,400 |
| loss counter | starts at 1 each half and overtime block; **+1 per loss (cap 5), −2 per win (floor 0)**; a loss pays the ladder at the new counter (96.7 % of team-rounds) |
| T loss after a plant | ladder **+ 600** |
| **CT team bonus** | **+50 per T killed in the round**, win or loss (capped at 5 kills) |
| planter / defuser | +300 personal |
| kill reward | 300 default; 600 SMGs (mac10, mp9, mp7, mp5sd, ump45, bizon) and xm1014; 900 nova, mag7, sawedoff; 100 awp; 1,500 knife; **100 taser (Zeus)**; **300 cz75a**; 300 p90 |
| cap | 16,000 |

Reconciliation (money at the decision → first row of the next round): exact 86.4 % (v30) / 87.4 % (v42) of
player-rounds; 96.2 % / 97.1 % when one personal credit (the deciding kill's reward, planter or defuser bonus) is
allowed. The ≥ 99 % target needs per-player credit tracking (follow-up).

## Ticks and merges (A-16)
Tick rate 64 in all matches (read `header.tick_rate`); `second` = tick/64 exactly; the tick channel covers ≥ 99.4 % of
ticks, largest gap 7 ticks (0.11 s). Merged event positions equal `player_vector` at the same tick for 99.6 % of kills,
never more than 1 tick stale.

## v30 vs v42 (A-39)
Same codes (weapons, sides, hit groups 0–8), same tick rate and economy. v30 needs: winner-side fix at half starts,
end-tick correction, event-derived end reasons, hit-box garbage filter, type-free rank scale (F-03). v42 adds
`player_connect`, `player_inputs`, `bullet_damage` and 9 more channels.
