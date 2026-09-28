"""Config loading. All tunables and game-rule constants live in ``configs/*.yaml``."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = REPO_ROOT / "configs"


def load_config(name: str, config_dir: Path | None = None) -> dict[str, Any]:
    """Load ``configs/<name>.yaml`` (``name`` without extension)."""
    path = (config_dir or CONFIG_DIR) / f"{name}.yaml"
    with path.open() as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping")
    return data


def config_hash(cfg: dict[str, Any]) -> str:
    """Stable short hash of a config dict, recorded in every experiment report."""
    payload = json.dumps(cfg, sort_keys=True, default=str).encode()
    return hashlib.sha256(payload).hexdigest()[:12]
