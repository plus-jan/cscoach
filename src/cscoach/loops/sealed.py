"""Split store and the only data path a modelling loop may use (docs/specs/07 §2, A-42).

``make_split`` writes ``<work_dir>/split.json`` once (match → train/calibration/test, K folds over the training
matches, seeds, and a content hash). ``LoopData`` hands out **training matches only** and appends every match id it
reads to ``<work_dir>/access.log``; requesting a sealed match raises ``SealedFoldError``. The guard checks the log and
the split hash, so a sealed read by any loop command fails the loop.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from cscoach.eval.splits import grouped_split, kfold_groups

SEALED = ("calibration", "test")


class SealedFoldError(RuntimeError):
    pass


def _hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def make_split(groups: pd.DataFrame, work_dir: Path, *, fractions: dict, k: int, seed: int) -> dict:
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    split = grouped_split(groups, fractions=fractions, seed=seed)
    train = sorted(m for m, s in split.items() if s == "train")
    body = {"seed": seed, "fractions": fractions, "k": k, "split": split, "folds": kfold_groups(train, k=k, seed=seed)}
    body["sha256"] = _hash({key: body[key] for key in ("seed", "fractions", "k", "split", "folds")})
    (work_dir / "split.json").write_text(json.dumps(body, sort_keys=True))
    return body


def load_split(work_dir: Path) -> dict:
    return json.loads((Path(work_dir) / "split.json").read_text())


def split_hash_ok(body: dict) -> bool:
    return body.get("sha256") == _hash({key: body[key] for key in ("seed", "fractions", "k", "split", "folds")})


class LoopData:
    def __init__(self, work_dir: Path, frame: pd.DataFrame, group_col: str = "match_id"):
        self.work_dir = Path(work_dir)
        self.body = load_split(self.work_dir)
        self.frame = frame
        self.group_col = group_col

    def _log(self, ids):
        with open(self.work_dir / "access.log", "a", encoding="utf-8") as f:
            for m in sorted(set(map(str, ids))):
                f.write(m + "\n")

    def read(self, match_ids) -> pd.DataFrame:
        ids = set(map(str, match_ids))
        sealed = sorted(m for m in ids if self.body["split"].get(m) in SEALED)
        self._log(ids)  # log first: a sealed request is recorded even though it is refused
        if sealed:
            raise SealedFoldError(f"loop requested {len(sealed)} sealed matches, e.g. {sealed[:3]}")
        return self.frame[self.frame[self.group_col].astype(str).isin(ids)]

    def training(self) -> pd.DataFrame:
        train = [m for m, s in self.body["split"].items() if s == "train"]
        df = self.read(train).copy()
        df["fold"] = df[self.group_col].astype(str).map(self.body["folds"])
        return df
