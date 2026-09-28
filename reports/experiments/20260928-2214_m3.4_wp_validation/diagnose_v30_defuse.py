"""M3.4 follow-up diagnosis (training matches only; sealed folds not read): post-plant rounds in which the T side is
eliminated. (1) CT win rate at the first T-wiped snapshot by time remaining, kit and channel set (WP table);
(2) for rounds won by a defuse after the T side was eliminated: whether snapshots exist after the elimination and
where decided_tick sits (CSDS player_death, player_info, bomb_state; 60 matches per channel set).
Run: uv run python reports/experiments/20260928-2214_m3.4_wp_validation/diagnose_v30_defuse.py <out_dir>
Data provided by PureSkill.gg."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from pureskillgg_dsdk.ds_io import DsReaderFs, GameDsLoader

from cscoach.data.features import side_table
from cscoach.data.quality import curator

out_dir = Path(sys.argv[1])
root = Path("/media/jan/merged/cs2coach")
s = pd.Series(json.load(open(root / "splits/wp_v1/split.json"))["split"])
train = sorted(s.index[s == "train"])
d = pd.read_parquet(root / "derived/wp_table_v1.parquet",
                    columns=["match_id", "round_uid", "tick", "ct_alive", "t_alive", "bomb_planted", "channel_set",
                             "y_ct_win", "time_remaining_s", "ct_kits"], filters=[("match_id", "in", train)])
x = d[(d.t_alive == 0) & d.bomb_planted & (d.ct_alive > 0)].sort_values("tick").drop_duplicates("round_uid")
x["time_bin"] = pd.cut(x.time_remaining_s, [-1, 5, 10, 20, 41]).astype(str)
x["kit"] = x.ct_kits > 0
t1 = x.groupby(["time_bin", "kit", "channel_set"]).y_ct_win.agg(rounds="size", ct_win="mean").reset_index()
t1.to_csv(out_dir / "diag_t_wiped_postplant_ct_win.csv", index=False)

cfg = yaml.safe_load(open("configs/features.yaml"))
cfg["code_side"] = {int(k): v for k, v in cfg["code_side"].items()}
hd = curator(cfg).get_dataframe(cfg["header_tome"]).set_index("match_id")
q = pd.read_parquet(root / "manifest/match_quality.parquet", columns=["match_id", "channel_set"])
q = q[q.match_id.isin(train)]
rows = []
for cs in ("v30", "v42"):
    for m in q[q.channel_set == cs].match_id.head(60):
        L = GameDsLoader(reader=DsReaderFs(root_path=str(root), manifest_key=hd.loc[m, "key"]))
        ch = L.get_channels([{"channel": "player_death", "columns": ["round", "tick", "player_id_fixed"]},
                             {"channel": "player_info", "columns": ["round", "player_id_fixed", "team_code"]},
                             {"channel": "bomb_state", "columns": ["round", "tick", "event_type"]}])
        sides = side_table(ch["player_info"], None, cfg).astype({"player_id_fixed": "float64"})
        dth = ch["player_death"].assign(player_id_fixed=ch["player_death"]["player_id_fixed"].astype("float64"),
                                        round=ch["player_death"]["round"].astype("int64"))
        dth = dth.merge(sides.assign(round=sides["round"].astype("int64")), on=["round", "player_id_fixed"], how="left")
        r = pd.read_parquet(root / "derived/rounds" / f"{m}.parquet", columns=["round", "winner_side", "decided_tick"]).set_index("round")
        f = pd.read_parquet(root / "derived/state_features" / f"{m}.parquet", columns=["round", "tick", "t_alive"])
        rate = int(hd.loc[m, "tick_rate"])
        for rd, ev in ch["bomb_state"].groupby("round"):
            de = ev[ev.event_type == "bomb_defused"]
            if not len(de) or rd not in r.index:
                continue
            dt_ = int(de.tick.iloc[0])
            td = dth[(dth["round"] == rd) & (dth["side"] == "T") & (dth["tick"] <= dt_)]
            if len(td) < 5:
                continue
            wipe = int(td.tick.max())
            fr = f[f["round"] == rd]
            rows.append({"channel_set": cs, "match_id": m, "round": int(rd), "winner": r.loc[rd, "winner_side"],
                         "wipe_to_defuse_s": (dt_ - wipe) / rate, "decided_minus_wipe_s": (r.loc[rd, "decided_tick"] - wipe) / rate,
                         "has_t_wiped_snapshot": bool((fr.t_alive == 0).any())})
t2 = pd.DataFrame(rows)
t2.to_csv(out_dir / "diag_defuse_rounds_after_t_wipe.csv", index=False)
summary = {"t_wiped_postplant_first_snapshot": t1.to_dict("records"),
           "defuse_after_t_wipe": t2.groupby("channel_set").agg(
               rounds=("round", "size"), ct_winner_share=("winner", lambda v: float((v == "CT").mean())),
               has_t_wiped_snapshot=("has_t_wiped_snapshot", "mean"), median_wipe_to_defuse_s=("wipe_to_defuse_s", "median"),
               median_decided_minus_wipe_s=("decided_minus_wipe_s", "median")).round(3).to_dict("index")}
(out_dir / "diag_summary.json").write_text(json.dumps(summary, indent=2, default=str))
print(json.dumps(summary["defuse_after_t_wipe"], indent=1))
