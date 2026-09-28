"""Thin wrapper around demoparser2 (https://github.com/LaihoE/demoparser).

M1.1: verify property/event names against the installed demoparser2 version on real
demos; they differ between versions. Configured names live in configs/data.yaml.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from cscoach.config import load_config


def match_id_for(path: Path) -> str:
    """Content hash of the demo file (first 16 hex chars of sha256)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


@dataclass
class ParsedDemo:
    match_id: str
    header: dict[str, Any]
    ticks: pd.DataFrame
    events: dict[str, pd.DataFrame] = field(default_factory=dict)

    def write(self, out_root: Path) -> Path:
        out = out_root / self.match_id
        out.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([self.header]).astype(str).to_parquet(out / "header.parquet")
        self.ticks.to_parquet(out / "ticks.parquet")
        for name, df in self.events.items():
            df.to_parquet(out / f"event_{name}.parquet")
        return out


def parse_demo(
    path: Path,
    player_props: list[str] | None = None,
    events: list[str] | None = None,
    tick_stride: int = 1,
) -> ParsedDemo:
    """Parse a ``.dem`` into header, (strided) player ticks and event tables."""
    try:
        from demoparser2 import DemoParser
    except ImportError as e:  # pragma: no cover
        raise ImportError('install parse extra: pip install -e ".[parse]"') from e

    cfg = load_config("data")["parse"]
    props = player_props or cfg["player_props"]
    wanted = events or cfg["events"]
    parser = DemoParser(str(path))
    header = dict(parser.parse_header())
    available = set(parser.list_game_events())
    ev: dict[str, pd.DataFrame] = {}
    for name in wanted:
        if name in available:
            ev[name] = pd.DataFrame(parser.parse_event(name, player=["X", "Y", "Z", "team_num"]))
    ticks = pd.DataFrame(parser.parse_ticks(props))
    if tick_stride > 1 and "tick" in ticks:
        ticks = ticks[ticks["tick"] % tick_stride == 0]
    return ParsedDemo(match_id_for(path), header, ticks.reset_index(drop=True), ev)
