"""Final WP fit (M3.3): the loop champion's GBDT on all training matches, its calibrator on the calibration fold.

docs/specs/03 WP models 2–3, docs/specs/04 §1/§7. The GBDT uses the M3.2 champion config (early stopping on a grouped
slice of the training matches); the calibrator (``cscoach.models.calibration``, the M3.3 loop choice) is fitted on
the GBDT's predictions for the calibration fold only. The fit reads **only** training and calibration matches
(``select_rows``; the table is read with a match filter) and records this in ``access.json``; the test fold and the
temporal holdout stay sealed for the single M3.4 evaluation. The loop's ``access.log`` is not touched, so its guard
still proves that no loop read a sealed match. Artefacts: ``booster.txt``, ``calibrator.json``, ``model.json``
(feature config, categories), ``card.json``. Data provided by PureSkill.gg.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import yaml

from cscoach.models.calibration import Calibrator
from cscoach.models.wp_gbdt import categories, fit_one, prepare

FIT_SPLITS = ("train", "calibration")


def select_rows(frame: pd.DataFrame, body: dict, splits=FIT_SPLITS) -> pd.DataFrame:
    if not set(splits) <= set(FIT_SPLITS):
        raise ValueError(f"the WP fit may read only {FIT_SPLITS}, not {sorted(set(splits) - set(FIT_SPLITS))}")
    return frame[frame["match_id"].astype(str).map(body["split"]).isin(splits)]


def fit(rows: pd.DataFrame, body: dict, model_cfg: dict, out_dir: Path, meta: dict | None = None) -> dict:
    gbdt, cal_cfg = model_cfg["gbdt"], model_cfg["calibration"]
    label = gbdt["label"]
    split = rows["match_id"].astype(str).map(body["split"])
    if not set(split.unique()) <= set(FIT_SPLITS):
        raise ValueError("rows outside the training and calibration folds were passed to the WP fit")
    train, cal = rows[split == "train"], rows[split == "calibration"]
    cats = categories(train, gbdt)
    booster, _ = fit_one(train, gbdt, cats)
    p_cal = booster.predict(prepare(cal, gbdt, cats)[0], num_iteration=booster.best_iteration)
    calibrator = Calibrator(cal_cfg).fit(p_cal, cal[label].to_numpy(), cal)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(out_dir / "booster.txt"), num_iteration=booster.best_iteration)
    (out_dir / "calibrator.json").write_text(json.dumps(calibrator.to_dict()))
    (out_dir / "model.json").write_text(json.dumps({"gbdt": gbdt, "categories": cats}, default=str))
    access = {"splits_read": sorted(set(split.unique())), "split_sha256": body["sha256"],
              "matches_read": {s: int(rows.loc[split == s, "match_id"].nunique()) for s in FIT_SPLITS}}
    (out_dir / "access.json").write_text(json.dumps(access, indent=2))
    keys = calibrator.keys(cal)
    group_rows = {} if keys is None else pd.Series(keys).value_counts().to_dict()

    def counts(df):
        c = {"matches": int(df["match_id"].nunique()), "rows": int(len(df))}
        if "round_uid" in df:
            c["rounds"] = int(df["round_uid"].nunique())
        return c

    card = {**(meta or {}), "split_sha256": body["sha256"], "train": counts(train), "calibration": counts(cal),
            "best_iteration": int(booster.best_iteration), "gbdt": gbdt, "calibration_cfg": cal_cfg,
            "calibrators": {"global": {"method": calibrator.global_.method, "rows": int(len(cal))},
                            **{k: {"method": c.method, "rows": int(group_rows.get(k, 0))}
                               for k, c in calibrator.groups_.items()}},
            "booster_sha256_12": hashlib.sha256((out_dir / "booster.txt").read_bytes()).hexdigest()[:12]}
    (out_dir / "card.json").write_text(json.dumps(card, indent=2, default=str))
    return card


class WPModel:
    def __init__(self, booster: lgb.Booster, gbdt: dict, cats: dict, calibrator: Calibrator):
        self.booster, self.gbdt, self.cats, self.calibrator = booster, gbdt, cats, calibrator

    @classmethod
    def load(cls, model_dir: Path) -> "WPModel":
        d = Path(model_dir)
        m = json.loads((d / "model.json").read_text())
        return cls(lgb.Booster(model_file=str(d / "booster.txt")), m["gbdt"], m["categories"],
                   Calibrator.from_dict(json.loads((d / "calibrator.json").read_text())))

    def predict(self, frame: pd.DataFrame, calibrated: bool = True) -> np.ndarray:
        p = self.booster.predict(prepare(frame, self.gbdt, self.cats)[0])
        return self.calibrator.predict(p, frame) if calibrated else p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, default=Path("configs/wp_calibration.yaml"))
    ap.add_argument("--report-dir", type=Path, required=True)
    ap.add_argument("--meta", type=json.loads, default={})
    args = ap.parse_args(argv)
    cfg = yaml.safe_load(args.config.read_text())
    loop, model = cfg["loop"], cfg["model"]
    body = json.loads((Path(loop["work_dir"]) / "split.json").read_text())
    ids = sorted(m for m, s in body["split"].items() if s in FIT_SPLITS)
    cols = list(dict.fromkeys([*loop["columns"], "round_uid"]))
    rows = select_rows(pd.read_parquet(loop["data"], columns=cols, filters=[("match_id", "in", ids)]), body)
    card = fit(rows, body, model, Path(cfg["fit"]["model_dir"]), meta=args.meta)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "card.json").write_text(json.dumps(card, indent=2, default=str))
    print(json.dumps({k: card[k] for k in ("train", "calibration", "best_iteration", "calibrators")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
