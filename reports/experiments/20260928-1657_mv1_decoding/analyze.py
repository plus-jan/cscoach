"""MV.1 analysis: recompute every number of report.md from the collector outputs.

Run: uv run python -m cscoach.verify.mv1 --out <root>/derived/mv1
     uv run python -m cscoach.verify.economy --mv1-dir <root>/derived/mv1
     uv run python <this file> <root>/derived/mv1 summary.json
(the rounds collector needs <root>/derived/rounds with decided_tick). Data provided by PureSkill.gg.
"""
import json, sys
import numpy as np, pandas as pd

src, out = sys.argv[1], sys.argv[2]
r = pd.read_parquet(f"{src}/rounds.parquet")
S = {"matches": int(r.match_id.nunique()), "rounds": int(len(r)),
     "matches_by_channel_set": r.drop_duplicates("match_id").channel_set.value_counts().to_dict(),
     "builds": sorted(int(b) for b in r.build_num.unique())}

v = r[r.channel_set == "v42"]
S["win_reason_v42"] = {f"{c} {m}": {"CT": int(((v.win_reason_code == c) & (v.winner_side == "CT")).sum()),
                                    "T": int(((v.win_reason_code == c) & (v.winner_side == "T")).sum())}
                       for c, m in v[["win_reason_code", "win_reason_message"]].drop_duplicates().itertuples(index=False)}
S["win_reason_v30"] = r[r.channel_set == "v30"].win_reason_code.value_counts().to_dict()

tr = r.tick_rate
bomb = ((r.bomb_exploded_tick - r.bomb_planted_tick) / tr).dropna()
S["bomb_timer_s"] = {"n": int(len(bomb)), "min": float(bomb.min()), "max": float(bomb.max())}
fr = ((r.freeze_end_tick - r.rs_round_start_tick) / tr)
per = r.assign(f20=fr.between(19.5, 20.5)).groupby("match_id").f20.mean()
S["freeze_matches_all_15s"] = int((per == 0).sum())
S["freeze_matches_mostly_20s"] = int((per >= 0.7).sum())
t42 = v[v.win_reason_code == 12]
S["round_time_v42_timeouts_s"] = sorted(set(((t42.end_tick - t42.freeze_end_tick) / t42.tick_rate).round(3)))
for cs in ("v42", "v30"):
    z = r[r.channel_set == cs]
    S[f"official_minus_end_ticks_{cs}"] = (z.rs_official_end_tick - z.end_tick).dropna().astype(int).value_counts().head(3).to_dict()

w = pd.read_parquet(f"{src}/weapons.parquet").groupby(["channel_set", "code", "weapon_name"]).n.sum().reset_index()
top = w.sort_values("n", ascending=False).drop_duplicates(["channel_set", "code"])
piv = top.pivot(index="code", columns="channel_set", values="weapon_name")
S["weapon_codes"] = {"v30": int(piv.v30.notna().sum()), "v42": int(piv.v42.notna().sum()),
                     "same_name_both": int((piv.v30 == piv.v42).sum())}
kh = pd.read_parquet(f"{src}/kill_hitboxes.parquet")
k42 = kh[kh.channel_set == "v42"]
S["headshot_kills_hitbox1_v42"] = [int(k42[(k42.hit_box_code == 1) & (k42.is_headshot == True)].n.sum()),
                                   int(k42[k42.hit_box_code == 1].n.sum())]
hb = pd.read_parquet(f"{src}/hitboxes.parquet")
h30 = hb[hb.channel_set == "v30"]
S["v30_hitbox_outside_0_8_share"] = float(h30[~h30.hit_box_code.between(0, 8)].n.sum() / h30.n.sum())

t = pd.read_parquet(f"{src}/ticks.parquet")
S["ticks"] = {"tick_rates": t.tick_rate.value_counts().to_dict(), "coverage_min": float((t.n_ticks / t.span).min()),
              "max_gap": int(t.max_gap.max()), "second_max_err": float(t.second_max_err.max()),
              "pos_exact_share": float(t.pos_lag_exact_share.mean()), "pos_lag_max": int(t.pos_lag_max.max())}

k = pd.read_parquet(f"{src}/economy_kills.parquet")
k = k[~k.team_kill.fillna(False).astype(bool)]
S["kill_reward_mode"] = {w_: int(g.delta.mode().iloc[0]) for w_, g in k.groupby("weapon_name") if len(g) >= 30}

e = pd.read_parquet(f"{src}/economy_rounds.parquet"); e["won"] = e.won.astype("boolean")
e = e.merge(r[["match_id", "round", "side_start_ct", "win_reason_code"]], on=["match_id", "round"])
rr = r.set_index(["match_id", "round"])
def simulate(g, dec):
    cnt = {"start_ct": 1, "start_t": 1}; o = {}
    for _, x in g.sort_values("round").iterrows():
        rd = x["round"]
        if rd == 13 or (rd > 24 and (rd - 25) % 3 == 0):
            cnt = {"start_ct": 1, "start_t": 1}
        loser = "start_t" if x.winner_team == "start_ct" else "start_ct"
        cnt[loser] = min(cnt[loser] + 1, 5); o[(rd, loser)] = cnt[loser]
        cnt[x.winner_team] = max(cnt[x.winner_team] - dec, 0)
    return o
e["team"] = np.where((e.side == "CT") == (e.side_start_ct == "CT"), "start_ct", "start_t")
lad = {1400: 1, 1900: 2, 2400: 3, 2900: 4, 3400: 5}
e["delta"] = e.money_next - e.money_end
lt = e[(e.won == False) & (e.side == "T") & (~e.planted)].assign(idx=lambda d: d.delta.map(lad))
lc = e[(e.won == False) & (e.side == "CT")].assign(idx=lambda d: (d.delta - 50 * d.enemy_deaths.clip(upper=5)).map(lad))
obs = pd.concat([lt, lc]).dropna(subset=["idx"]).groupby(["match_id", "round", "team"]).idx.agg(lambda s: s.mode().iloc[0]).reset_index()
for dec in (1, 2):
    sims = {m: simulate(g, dec) for m, g in r.groupby("match_id")}
    S[f"loss_counter_match_dec{dec}"] = float(np.mean([sims[m].get((rd, tm)) == i for m, rd, tm, i in
                                                        zip(obs.match_id, obs["round"], obs.team, obs.idx)]))
sims = {m: simulate(g, 2) for m, g in r.groupby("match_id")}
code_reason = {1: "exploded", 7: "defused", 8: "elimination", 9: "elimination", 12: "time"}
WIN = {"elimination": 3250, "time": 3250, "defused": 3500, "exploded": 3500}; LAD = [None, 1400, 1900, 2400, 2900, 3400]
def reward(x):
    if pd.isna(x.won) or x.reason == "other":
        return np.nan
    if x.won:
        base = WIN[x.reason]
    else:
        i = sims[x.match_id].get((x["round"], x.team))
        if i is None:
            return np.nan
        base = LAD[i] + (600 if (x.side == "T" and x.planted) else 0)
    return base + (50 * min(x.enemy_deaths, 5) if x.side == "CT" else 0)
for cs in ("v30", "v42"):
    z = e[e.channel_set == cs].copy()
    if cs == "v42":
        z["reason"] = z.win_reason_code.map(code_reason).fillna("other")
    z["pred"] = z.apply(reward, axis=1)
    z = z[(~z.next_is_half_start) & z.pred.notna()]
    d = z.money_next - np.minimum(z.money_end + z.pred, 16000)
    S[f"money_reconciliation_{cs}"] = {"player_rounds": int(len(z)), "exact": float((d == 0).mean()),
                                       "one_credit": float(d.isin([0, 100, 300, 600, 900, 1500]).mean())}
S["half_start_money"] = e[e.next_is_half_start].money_next.value_counts().head(2).to_dict()
def clean(o):
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o.item() if hasattr(o, "item") else o
S = clean(S)
json.dump(S, open(out, "w"), indent=1, default=str)
print(json.dumps(S, indent=1, default=str)[:4000])
