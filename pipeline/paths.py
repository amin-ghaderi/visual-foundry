"""Project-root and relative path helpers."""

from __future__ import annotations

from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
ROOT = PIPELINE_DIR.parent


def resolve_under_root(relative: str | Path) -> Path:
    path = Path(relative)
    if path.is_absolute():
        return path
    return (ROOT / path).resolve()


def require_file(path: Path, what: str) -> Path:
    if not path.is_file():
        raise FileNotFoundError(f"{what} not found: {path}")
    return path


def require_dir(path: Path, what: str) -> Path:
    if not path.is_dir():
        raise FileNotFoundError(f"{what} not found: {path}")
    return path
