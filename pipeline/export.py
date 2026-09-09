"""Record export intent. Actual PNG export is done from Figma MCP by Cursor."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import yaml

_PIPELINE = Path(__file__).resolve().parent
if str(_PIPELINE) not in sys.path:
    sys.path.insert(0, str(_PIPELINE))

from config import load_config
from project import format_version, load_project, project_dir, save_project


def planned_export_name(data: dict) -> str:
    cfg = load_config()
    pattern = str(cfg.get("export", {}).get("name_pattern") or "{template}-{project_id}-{version}.{format}")
    fmt = str(cfg.get("export", {}).get("format") or "png")
    return pattern.format(
        template=data.get("template") or "design",
        project_id=data["project_id"],
        version=format_version(int(data.get("current_version") or 1)),
        format=fmt,
    )


def export_status(project_id: str) -> dict:
    data = load_project(project_id)
    root = project_dir(project_id)
    name = planned_export_name(data)
    dest = root / "exports" / name
    figma_meta = root / "figma" / "figma.yaml"
    meta = {}
    if figma_meta.is_file():
        loaded = yaml.safe_load(figma_meta.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            meta = loaded
    status = {
        "project_id": project_id,
        "planned_filename": name,
        "planned_path": str(dest.relative_to(root)),
        "exists": dest.is_file(),
        "figma_file_key": meta.get("figma_file_key", ""),
        "frame_id": meta.get("frame_id", ""),
        "frame_name": meta.get("frame_name", ""),
        "note": (
            "Cursor exports the approved Figma frame via Figma MCP into this path. "
            "This command does not rasterize Figma itself."
        ),
        "updated_at": date.today().isoformat(),
    }
    if dest.is_file():
        data["latest_export"] = f"exports/{name}"
        save_project(data)
        status["latest_export"] = data["latest_export"]
    return status


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show or record the export path for a project.")
    parser.add_argument("--project", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        status = export_status(args.project)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(yaml.safe_dump(status, sort_keys=False, allow_unicode=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
