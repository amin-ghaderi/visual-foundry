"""Create the next sequential project folder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PIPELINE = Path(__file__).resolve().parent
if str(_PIPELINE) not in sys.path:
    sys.path.insert(0, str(_PIPELINE))

from config import load_config
from paths import ROOT
from project import (
    default_project_yaml,
    ensure_project_dirs,
    next_project_id,
    normalize_project_id,
    project_dir,
    save_project,
    templates_dir,
    used_project_ids,
)


def create_project(template: str | None = None, requested_id: str | None = None) -> dict:
    cfg = load_config()
    template_name = template or str(cfg.get("default_template") or "memorial")
    template_root = templates_dir() / template_name
    if not template_root.is_dir():
        raise FileNotFoundError(f"Template not found: {template_root}")

    if requested_id:
        pid = normalize_project_id(requested_id)
        if pid in used_project_ids() or project_dir(pid).exists():
            raise FileExistsError(f"Project {pid} already exists. IDs are never reused.")
    else:
        pid = next_project_id()
        if project_dir(pid).exists():
            raise FileExistsError(f"Project {pid} already exists.")

    root = ensure_project_dirs(pid)
    data = default_project_yaml(pid, template_name)
    save_project(data)
    (root / "input" / ".gitkeep").write_text("", encoding="utf-8")
    (root / "prepared" / ".gitkeep").write_text("", encoding="utf-8")
    (root / "handoff" / ".gitkeep").write_text("", encoding="utf-8")
    (root / "figma" / ".gitkeep").write_text("", encoding="utf-8")
    (root / "exports" / ".gitkeep").write_text("", encoding="utf-8")
    (root / "versions" / ".gitkeep").write_text("", encoding="utf-8")
    return data


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the next project ID folder.")
    parser.add_argument("--template", default=None, help="Template name (default from config.yaml)")
    parser.add_argument(
        "--id",
        dest="requested_id",
        default=None,
        help="Optional explicit ID. Fails if it already exists.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        data = create_project(template=args.template, requested_id=args.requested_id)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    root = project_dir(data["project_id"])
    print(f"Created {data['project_id']}")
    print(f"Template: {data['template']}")
    print(f"Path: {root.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
