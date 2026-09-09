"""Deterministic version helpers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PIPELINE = Path(__file__).resolve().parent
if str(_PIPELINE) not in sys.path:
    sys.path.insert(0, str(_PIPELINE))

from project import format_version, load_project, save_project


def bump_version(project_id: str) -> dict:
    data = load_project(project_id)
    current = int(data.get("current_version") or 1)
    data["current_version"] = current + 1
    save_project(data)
    return data


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show or bump a project version.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--bump", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data = bump_version(args.project) if args.bump else load_project(args.project)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"{data['project_id']} {format_version(int(data['current_version']))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
