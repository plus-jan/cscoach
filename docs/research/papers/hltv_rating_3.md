---
id: hltv_rating_3
title: HLTV Rating 3.0 (Introducing Rating 3.0; Rating 3.0 adjustments) + Skin.Club
  explainer
authors: NER0cs (HLTV); 'magic' (Skin.Club)
year: 2025
venue: HLTV.org news articles; Skin.Club community article
url: https://www.hltv.org/news/42485/introducing-rating-30
also:
- https://www.hltv.org/news/43047/rating-30-adjustments-go-live
- https://community.skin.club/en/news/hltv-rating-3-0-cs2-update
license: notes are user-written paraphrases; original articles © HLTV / Skin.Club
  — do not copy originals here
content_type: paraphrased notes (secondary), provided by the project owner 2026-09-28
---

# HLTV Rating 3.0 — Round Swing and eco-adjustment

> **Not a full text.** Paraphrased notes on HLTV/Skin.Club articles supplied by the project owner. Consult the original articles before quoting numbers.

<!-- cscoach-notes:start -->
## cscoach notes (hand-written — preserved on re-conversion)
**Provenance:** the project owner's paraphrased notes on two HLTV articles (20 Aug 2025, 29 Oct 2025) and one
Skin.Club explainer (21 Aug 2025). They are not the articles themselves. Numbers are as reported by
HLTV for **pro CS2**, and the formula is not published in full.

- **Relevance:** high as the **industry reference** for WP-based kill value (Round Swing),
  economy-adjusted stats and credit splitting (M5, M6, A-17, A-23).
- **Claims (from the notes):**
  - Six sub-ratings: Kills, Damage, Survival, KAST, Multi-Kills, Round Swing; Impact was removed.
    After the Oct 2025 adjustment: output/cost weights back to 60/40, Kills up and Swing down (community
    figures: Kills ~25%, Swing ~33%).
  - **Round Swing:** the change in round WP per kill, given economy, bomb, players alive and map/side
    baselines. Opening kill ≈ +20%, a 1v1 clutch ≈ +50%, anti-eco kills worth little. Elite season
    averages ≈ +4% per round; most players within ±1.5%.
  - **Credit split:** final blow, damage share, flash assists, trades. After the adjustment: less
    weight on the final blow, more on damage, trades and flashes.
  - **Round end when the losers survive** (save, time, bomb): the remaining swing is shared as clutcher
    ×1, players with swing from kills ×2, defuser ×1, alive at round end ×1. **Saving players take the
    same hit as losing the clutch.**
  - **Eco-adjustment:** equipment = armour + most expensive weapon, bucketed from sniper down to starter
    pistol. Only **44.7%** of duels are same-bucket. Kill points ∝ duel difficulty (e.g. T rifle vs rifle
    ~48% win → ~1.10; vs starter pistol ~75% → ~0.54). AWPers win ~56% (T) / ~60% (CT) of duels vs
    riflers. Applies to kills, damage, survival, KAST and multi-kills.
  - Rule details: assist threshold 40 damage; **trade window 5 s** (trade denials, failed trades);
    opening deaths penalised as much as opening kills are rewarded.
  - **HLTV's own caveats:** Swing ignores game state beyond these features, player HP and kill
    location; it can be dominated by single rounds in small samples; the rating is tuned for
    event-length samples; periodic recalibration is planned, notably **after Valve's CS2 economy update
    around Aug 2025**.
- **Corrections vs. synthesis:** "entry ≈ +20%" and "clutch up to 50%" match HLTV (1v1 ≈ +50%, harder
  clutches more). The synthesis cites the Skin.Club article as the source; the primary source is HLTV.
- **Use in project:**
  - Our WPA ≈ Round Swing, with a better-specified WP (HP, time, positions) and calibration evidence.
    Their end-of-round share rule is a candidate for the **round-end residual credit** (docs/specs/03
    #wpa, A-23).
  - Eco-adjusted kill value = 1 − P(win duel). Our xK gives this directly per duel, with tier-specific
    calibration instead of pro bucket averages (M4, M5.2).
  - Their trade window (5 s) is a *convention*, not evidence; A-17 is still estimated in MV.6.
  - **Economy update around Aug 2025 falls inside the CSDS window (from 2025-07-18)** → A-13 must be
    checked per `build_num` (MV.1).
  - Small-sample instability of swing-type metrics → our within-match shrinkage and gates (A-07, A-26).
- **Caveats:** paraphrased secondary notes; proprietary formula; pro-only calibration; no uncertainty
  reported.
<!-- cscoach-notes:end -->

## Source notes (user-provided paraphrases — NOT full text)

### HLTV — Introducing Rating 3.0 (primary, 20 Aug 2025)

Notes: HLTV — "Introducing Rating 3.0"

- **Source:** https://www.hltv.org/news/42485/introducing-rating-30
- **Author:** NER0cs (HLTV) · **Published:** 20 Aug 2025
- **Type:** Paraphrased notes, not a copy of the article. Read the original for full text, charts and tables.

#### TL;DR
Rating 3.0 replaced 2.1 across all CS2 matches on HLTV. It keeps a 2.1-style core but eco-adjusts it, and adds a new win-probability metric, **Round Swing**. HLTV calls it the largest rating overhaul since 2.0 (2017). The event average is still 1.00.

#### Structure
Six sub-ratings (2.1 had five):

| Sub-rating | What changed |
|---|---|
| Kills | Eco-adjusted by duel win rate (map, side, both players' equipment) |
| Damage | Eco-adjusted the same way |
| Survival | Eco-adjusted the same way |
| KAST | Eco-adjusted by how likely that outcome is given map, side, own gear and the enemy team's average gear |
| Multi-Kills | New standalone sub-rating, eco-adjusted like KAST |
| Round Swing | New — change in round win probability per kill |

**Impact is gone.** Round Swing covers most of what it measured (openers, clutches); Multi-Kill rating keeps the "explosive round" element.

#### Other rule changes
- Assists go back to the CS:GO threshold of 40 damage (was 25).
- New concepts inside the sub-ratings: **trade denials** (two kills within 5 s) and **failed trades** (if both players die within 5 s, the second player is penalised and the first rewarded).
- Opening deaths are now penalised as much as opening kills are rewarded (2.1 rewarded openers more than it punished opening deaths).

#### Economy adjustment
- Equipment value = armour + most expensive weapon, bucketed roughly into: sniper, tier-1 rifles, tier-2 rifles, SMGs/shotguns, upgraded pistols, starter pistols.
- Only **44.7%** of duels happen between players in the same bucket, so most kills involve an economy mismatch.
- HLTV computed head-to-head win rates between buckets; a harder duel earns more "kill points", an easier one fewer.
- Example (T side): rifle vs rifle (~48% win rate) ≈ 1.10 kill points; killing a starter-pistol player (~75%) ≈ 0.54.
- Works in reverse too: low-value gear killing full-buy players earns extra.
- Eco frags still count (pistols are strong), just much less.
- **AWP effect:** AWPers win ~56% (T) / ~60% (CT) of duels vs riflers, so eco-adjustment trims their kill value. HLTV argues they weren't overrated before and can still score well via favourable duels and Round Swing.
- Stats pages get a toggle for eco-adjusted figures; the coloured bars reflect the sub-rating, not the raw number shown (so 0.70 KPR can show yellow while 0.68 shows green).

#### Round Swing
- For each kill, measures the change in the team's round-win probability, using economy, bomb state, players alive, and map-specific CT/T win rates.
- Credit is split by final blow, damage share, flash assists, and whether the kill was a trade.
- Reported per round as a percentage. Elite season values ≈ +4% (2025 at time of writing: donk +3.79%, ZywOo +3.69%); most players sit between −1.5% and +1.5% over large samples. Single maps/events swing much wider.
- Context matters: kills in 3v3/2v2 count more than in 5v2/4v1; against a full eco where the win chance is ~96%, the whole team can only gain ~4% in total.
- Rewards "bailing out" a round that teammates put at risk, even with superior gear.
- Opening kill ≈ +20%; winning a 1v1 clutch ≈ +50% (harder clutches more).
- **Saves:** if losers save after, say, a T-side double entry, the remaining probability is credited to the players who contributed (split by contribution). Saving players take the same hit as losing the clutch — the reward for saving is the weapon, not rating.

### Why it's not 100% of the rating
- Diminishing returns on multi-kills (5v5→5v3 is huge; 4v2→4v0 is small) — statistically correct, but HLTV still wants to credit explosive plays, hence the separate Multi-Kill rating.
- Early-round actions look small next to late-round clutches; HLTV wants them to count for more when judging "best player".
- Round Swing slightly favours passive players (often AWPers), which HLTV says is offset by eco-adjustment being kinder to riflers.

#### Who moves
- **Down:** high-activity aggressive riflers who farm anti-ecos and give away man-advantages — examples named: xertioN, malbsMd, YEKINDAR.
- **Up:** disciplined, clutch-capable support riflers — Jimpphat, Techno.
- **AWPers mixed:** nqz up; device and 910 down.
- **Mid-round specialists** (e.g. Twistzz) benefit; players on high-win-rate teams (e.g. apEX) find it harder to coast.

#### Worked example
FaZe vs BetBoom map: EliGE had 23 kills / 133 ADR and a **2.06** in 2.1. Nine kills came vs full ecos and three vs half-buys. After eco-adjustment he drops to **1.40** (still decent thanks to a 4-1 in pistol duels and 84 ADR in gun-vs-gun rounds), letting broky (solid game plus a 1v2 clutch) edge ahead.

#### Where it shows up
- Refreshed player stats page: T/CT rating at the top, Multi-Kill where Impact used to be, a new Round Swing slot, clearer list of maps in the sample.
- Match pages: Swing and 3.0 on the scoreboard; box scores gain openers, multi-kills and clutches.
- Performance tabs, player-of-the-match and MVP boxes show Multi-Kill rating and Round Swing.
- Planned: eco-adjustment and Swing in the "attributes" section.

#### Rating history (brief)
- **1.0 (2010):** by Petar "Tgwri1s" Milovanovic — kills, deaths and multi-kills.
- **2.0 (2017):** added KAST, Damage, and an Impact rating (openers, clutches, multis).
- **2.1 (2024):** recalibrated for CS2 and penalised saving.
- **3.0 (2025):** eco-adjustment + Round Swing. Rating underpins HLTV's MVPs and Top 20.

### HLTV — Rating 3.0 adjustments go live (primary, 29 Oct 2025)

Notes: HLTV — "Rating 3.0 adjustments go live"

- **Source:** https://www.hltv.org/news/43047/rating-30-adjustments-go-live
- **Author:** NER0cs (HLTV) · **Published:** 29 Oct 2025
- **Type:** Paraphrased notes, not a copy of the article. Read the original for full text, charts and tables.

#### TL;DR
About two months after launch, HLTV re-weighted Rating 3.0 to give **kills more weight and Round Swing less**, mainly to fix odd single-map results. Year-long ratings barely move (most players ±0.02). NER0 confirmed in the comments that this is effectively "3.0.1", not 3.1.

#### Why
- Round Swing was meant to be an impact *modifier* on top of a conventional rating, but in small samples it dominated the final number.
- Context-driven quirks confused people: finishing kills in 4v1/5v2 count for little, big clutches can swing a single-map rating heavily, and map-level averages mean e.g. T-side kills on Overpass count more than CT-side.
- HLTV acknowledges Swing still ignores game state, player HP and kill location, and can be skewed by one huge round.
- Goal: punish low-impact games, but still reward high-output, active play.

#### Changelog
- Eco-adjustment toggle added to match scoreboards.
- Sub-rating weights changed: **Swing down, Kills up**; KAST and Multi-Kill reduced (Multi-Kill overlaps heavily with Kills).
- Within Swing, less weight on the final blow; more on damage share, trades and flash assists.
- Eco-adjusted KAST transformed to be fairer to the winning team.
- Eco-adjusted damage recalculated (kinder to AWPers).
- End-of-round Swing shared among more contributors on the winning team.
- Underlying constants updated.

### Output vs cost balance
Rating 2.0 split roughly **60/40** between output (kills, damage, impact) and cost (KAST, survival). The launch version of 3.0 was ~56/44; the adjustment restores 60/40.

*Weight figures discussed in the comments (not stated in the article body, so treat as community-reported): Kills ~12% → ~25%, Swing ~40% → ~33%, Survival ~15%, KAST ~8%, Multi-Kills ~4%.*

#### End-of-round Swing distribution
Applies when losers survive (time runs out, bomb explodes, or bomb is defused).

| Before | After (shares) |
|---|---|
| Clutch winner took 100% of remaining Swing; otherwise split by positive Swing from kills | Clutcher ×1 · players with Swing from kills ×2 · bomb defuser ×1 · players alive at round end ×1 |

Context: HLTV had earlier loosened clutch rules so kill-less clutches (ninja defuses, running down the bomb timer) count. That occasionally over-credited "fake" clutches; a manual override exists but is a last resort. The share system is meant to reduce reliance on it.

#### Eco-adjustment tweaks
- Because Swing lost weight, eco-adjusted damage was eased so AWPers (who tend to have lower ADR) aren't underrated.
- Eco-adjusted KAST had inflated **losing** teams over single maps (their eco/force-round actions counted extra). Its strength was cut significantly; AWPers are back at the top of that sub-rating.
- The rating is optimised for event-length samples, where giving worse-equipped players a boost is appropriate.

#### New scoreboard toggle
- **eK-eD:** eco-adjusted kill/death (e.g. an anti-eco kill ≈ 0.50, dying with an AK to a Glock ≈ 1.50), rounded to look like a normal K-D. If you're favoured in a duel you gain less for winning and lose more for losing.
- **eADR:** same logic for damage.
- **eKAST:** more KAST points when that outcome was less likely for your economy. (NER0 in comments: ~0.55 points for a KAST with an AK vs an eco, ~1.21 with a pistol vs a full buy; averages out to normal KAST% over an event.)
- The +/- K-D column was removed from scoreboards to make room (a frequent complaint in the comments).

#### Example
FaZe vs Liquid, Cologne 2025: frozen's high output (1.21 eKPR, 84 eADR) now rates above ultimate's high-impact but losing performance (+9.10% Swing, 0.71 eKPR).

#### Effects
- All past matches recalculated with the new formula, in time for the 2025 Top 20.
- EVPs awarded before 3.0's July introduction are being re-evaluated.
- Most players move very little over large samples; notable exception is donk, whose 1.59 Kill Rating lifts him about +0.04.
- HLTV plans periodic recalibration, especially after Valve's economy update that landed around 3.0's launch.

### Skin.Club explainer (secondary)

Notes: Skin.Club — "HLTV launches Rating 3.0: a revolution in evaluating CS2 players"

- **Source:** https://community.skin.club/en/news/hltv-rating-3-0-cs2-update
- **Author:** "magic" (Skin.Club community) · **Published:** 21 Aug 2025
- **Type:** Paraphrased notes, not a copy of the article.

#### What it is
A secondary write-up published the day after HLTV's launch article. It mostly restates HLTV's explanation, then adds a short pros/cons opinion section and a round-up of HLTV forum reactions. No original data.

#### Content summary
- **Framing:** biggest rating change since 2.0 (2017); all CS2 matches now use it; combines economic context with Round Swing.
- **History recap:** 1.0 (2010, Tgwri1s, added multi-kills to K/D) → 2.0 (2017, KAST/Damage/Impact) → 2.1 (2024, CS2 recalibration, penalties for saving and passive AWPing) → 3.0 (2025).
- **Six sub-ratings:** Kills, Damage, Survival, KAST, Multi-Kills, Round Swing; Impact removed and split between Swing and Multi-Kill.
- **Economy adjustment:** cites the "~55% of duels are mismatched" point (the inverse of HLTV's 44.7% same-bucket figure). Anti-eco kills worth less, even duels standard, low-gear wins vs strong gear get a bonus.
- **Round Swing:** ~20% for an entry in a 5v5, up to ~50% for a 1v1/1v2 clutch, minimal for kills in 5v2s or vs full ecos; credit split across final blow, damage, flashes and trades.
- **EliGE example:** 2.06 → 1.40 after eco-adjustment; broky overtakes.
- **Who gains/loses:** same list as HLTV (xertioN, malbsMd, YEKINDAR down; Jimpphat, Techno up; nqz up, device and 910 down; Twistzz up; apEX harder to coast).

#### Skin.Club's own take
- **Pros:** fairer handling of eco frags; better balance across roles; more real match context.
- **Cons:** openers can look undervalued next to clutches; harder for fans to read at a glance.

#### Community reaction section
Summarises HLTV comment-thread sentiment as split: some enthusiastic ("3.0 > 2.1" style praise), some joking, much of it filtered through the donk vs ZywOo debate, plus accusations that the formula was tuned for or against specific stars.

#### Caveats
- Contains a small inaccuracy vs HLTV's own wording: it says survival "in difficult situations" is now rewarded more — HLTV only says survival is eco-adjusted.
- Published before the October 2025 re-weighting, so it doesn't reflect those changes.

