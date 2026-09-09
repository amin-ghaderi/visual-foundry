"""Project ID allocation, project.yaml, and LATEST.md."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from config import load_config
from paths import ROOT

PROJECT_ID_RE = re.compile(r"^P(\d{3,})$")
SUBDIRS = ("input", "prepared", "handoff", "figma", "exports", "versions")


def projects_dir() -> Path:
    return ROOT / load_config()["paths"]["projects"]


def archive_dir() -> Path:
    return ROOT / load_config()["paths"]["archive"]


def templates_dir() -> Path:
    return ROOT / load_config()["paths"]["templates"]


def project_dir(project_id: str) -> Path:
    pid = normalize_project_id(project_id)
    return projects_dir() / pid


def normalize_project_id(value: str) -> str:
    text = value.strip().upper()
    if not PROJECT_ID_RE.fullmatch(text):
        raise ValueError(f"Invalid project id {value!r}. Expected P001, P002, …")
    return text


def used_project_ids() -> set[str]:
    found: set[str] = set()
    for base in (projects_dir(), archive_dir(), ROOT / "archive"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_dir() and PROJECT_ID_RE.fullmatch(path.name):
                found.add(path.name)
    return found


def next_project_id() -> str:
    used = used_project_ids()
    numbers = [int(PROJECT_ID_RE.fullmatch(pid).group(1)) for pid in used]
    nxt = (max(numbers) if numbers else 0) + 1
    return f"P{nxt:03d}"


def default_project_yaml(project_id: str, template: str) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "status": "draft",
        "current_version": 1,
        "template": template,
        "latest_asset": "",
        "latest_handoff": "",
        "latest_figma": "",
        "latest_export": "",
        "created_at": date.today().isoformat(),
        "updated_at": date.today().isoformat(),
    }


def load_project(project_id: str) -> dict[str, Any]:
    path = project_dir(project_id) / "project.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"project.yaml not found for {project_id}: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid project.yaml: {path}")
    return data


def save_project(data: dict[str, Any]) -> Path:
    pid = normalize_project_id(str(data["project_id"]))
    data["project_id"] = pid
    data["updated_at"] = date.today().isoformat()
    path = project_dir(pid) / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    write_latest_md(data)
    return path


def format_version(n: int) -> str:
    cfg = load_config()
    width = int(cfg.get("versioning", {}).get("width", 2))
    prefix = str(cfg.get("versioning", {}).get("prefix", "v"))
    return f"{prefix}{n:0{width}d}"


def write_latest_md(data: dict[str, Any]) -> Path:
    pid = data["project_id"]
    version = format_version(int(data.get("current_version") or 1))
    lines = [
        f"# {pid} — latest",
        "",
        f"- Status: `{data.get('status', 'draft')}`",
        f"- Template: `{data.get('template', '')}`",
        f"- Version: `{version}`",
        f"- Asset: `{data.get('latest_asset') or '(none)'}`",
        f"- Handoff: `{data.get('latest_handoff') or '(none)'}`",
        f"- Figma: `{data.get('latest_figma') or '(none)'}`",
        f"- Export: `{data.get('latest_export') or '(none)'}`",
        "",
        "This file is generated from `project.yaml`. Do not duplicate large PNGs to mark latest.",
        "",
    ]
    path = project_dir(pid) / "LATEST.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def format_status(data: dict[str, Any]) -> str:
    pid = data["project_id"]
    root = project_dir(pid)
    version = format_version(int(data.get("current_version") or 1))
    asset = data.get("latest_asset") or ""
    export = data.get("latest_export") or ""
    figma_meta = root / "figma" / "figma.yaml"
    figma_name = ""
    if figma_meta.is_file():
        meta = yaml.safe_load(figma_meta.read_text(encoding="utf-8")) or {}
        figma_name = str(meta.get("figma_file_name") or meta.get("frame_name") or "")

    input_files = sorted(p.name for p in (root / "input").glob("*") if p.is_file())
    validation = "UNKNOWN"
    report = ROOT / "reports" / pid / "validate.json"
    if report.is_file():
        vdata = yaml.safe_load(report.read_text(encoding="utf-8")) or {}
        validation = str(vdata.get("status") or vdata.get("quality_gate") or "UNKNOWN")

    lines = [
        pid,
        f"Status: {str(data.get('status', 'draft')).upper()}",
        f"Template: {data.get('template') or '(none)'}",
        f"Version: {version}",
        f"Input: {', '.join(input_files) if input_files else '(none)'}",
        f"Image: {asset or '(none)'}",
        f"Handoff: {data.get('latest_handoff') or '(none)'}",
        f"Figma: {figma_name or data.get('latest_figma') or '(none)'}",
        f"Export: {export or '(none)'}",
        f"Validation: {validation}",
    ]
    return "\n".join(lines)


def ensure_project_dirs(project_id: str) -> Path:
    root = project_dir(project_id)
    for name in SUBDIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root
