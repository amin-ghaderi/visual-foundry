"""Load project-root config.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from paths import ROOT, resolve_under_root


CONFIG_PATH = ROOT / "config.yaml"


@lru_cache(maxsize=1)
def load_config(path: Path | None = None) -> dict[str, Any]:
    target = path or CONFIG_PATH
    if not target.is_file():
        raise FileNotFoundError(f"config.yaml not found: {target}")
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"config.yaml must be a mapping: {target}")
    return data


def config_path(key: str, cfg: dict[str, Any] | None = None) -> Path:
    cfg = cfg or load_config()
    relative = cfg.get("paths", {}).get(key)
    if not relative:
        raise KeyError(f"config.yaml paths.{key} is missing")
    return resolve_under_root(relative)
