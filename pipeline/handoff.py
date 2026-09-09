"""Interpret a Design Handoff without inventing creative content."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

_PIPELINE = Path(__file__).resolve().parent
if str(_PIPELINE) not in sys.path:
    sys.path.insert(0, str(_PIPELINE))

from config import load_config
from project import format_version, load_project, project_dir, save_project

CREATIVE_KEYS = (
    "objective",
    "composition",
    "layout",
    "hierarchy",
    "typography",
    "colors",
    "imagery",
    "image_treatment",
    "content",
    "references",
    "restrictions",
    "requested_changes",
    "template_requirements",
)
TECHNICAL_KEYS = (
    "canvas_size",
    "spacing",
    "alignment",
    "template",
    "export",
)
CONTENT_FIELD_LABELS = {
    "persian_name": ("persian name", "name fa", "نام"),
    "english_name": ("english name", "name en"),
    "birth_date": ("birth", "born", "birth year", "birth date"),
    "death_date": ("death", "died", "death year", "death date"),
    "location": ("location", "place"),
    "identifier": ("identifier", "id", "archive id"),
    "memorial_statement_fa": ("statement fa", "statement (fa)", "persian statement"),
    "memorial_statement_en": ("statement en", "statement (en)", "english statement"),
    "biography_fa": ("biography fa", "biography (fa)"),
    "biography_en": ("biography en", "biography (en)"),
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _maybe_json(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    if stripped[0] not in "{[":
        return None
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _maybe_yaml(text: str) -> dict[str, Any] | None:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^#+\s*{re.escape(heading)}\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(text)
    if not match:
        return ""
    start = match.end()
    nxt = re.search(r"^#+\s+", text[start:], re.MULTILINE)
    end = start + nxt.start() if nxt else len(text)
    return text[start:end].strip()


def _labeled_value(text: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        pattern = re.compile(
            rf"^[\-*]?\s*{re.escape(label)}\s*[:：]\s*(.+)$",
            re.IGNORECASE | re.MULTILINE,
        )
        match = pattern.search(text)
        if match:
            value = match.group(1).strip().strip("`")
            if value and value.lower() not in {"(none)", "none", "n/a", "tbd", "—", "-"}:
                return value
    return ""


def interpret_text(text: str, filename: str = "") -> dict[str, Any]:
    cfg = load_config()
    parsed = _maybe_json(text) or _maybe_yaml(text) or {}
    creative = {k: parsed.get(k, "") for k in CREATIVE_KEYS}
    technical = {k: parsed.get(k, "") for k in TECHNICAL_KEYS}

    if not technical.get("template"):
        technical["template"] = _labeled_value(text, ("template",)) or cfg.get(
            "default_template", "memorial"
        )
    if not technical.get("canvas_size"):
        canvas = cfg.get("default_canvas") or {}
        from_text = _labeled_value(text, ("canvas", "canvas size"))
        technical["canvas_size"] = from_text or f"{canvas.get('width')} × {canvas.get('height')}"

    content: dict[str, str] = {}
    for field, labels in CONTENT_FIELD_LABELS.items():
        value = ""
        if isinstance(parsed.get("content"), dict):
            value = str(parsed["content"].get(field) or "")
        if not value:
            value = str(parsed.get(field) or "")
        if not value:
            value = _labeled_value(text, labels)
        content[field] = value

    if not creative.get("objective"):
        creative["objective"] = _section(text, "Objective") or _section(text, "Goal")
    if not creative.get("restrictions"):
        creative["restrictions"] = _section(text, "Restrictions") or _section(text, "Do not")
    if not creative.get("requested_changes"):
        creative["requested_changes"] = _section(text, "Changes") or _section(text, "Requested changes")
    if not creative.get("imagery"):
        creative["imagery"] = _section(text, "Imagery") or _section(text, "Images")

    return {
        "source_file": filename,
        "creative_requirements": creative,
        "technical_requirements": technical,
        "content_fields_found": content,
        "content_fields_empty": [k for k, v in content.items() if not v],
        "notes": [
            "Empty creative fields were left empty.",
            "Missing technical values were filled from config.yaml / template defaults.",
            "No names, dates, slogans, or biography were invented.",
        ],
    }


def interpret_project(project_id: str) -> dict[str, Any]:
    data = load_project(project_id)
    handoff_dir = project_dir(project_id) / "handoff"
    sources = [
        p
        for p in sorted(handoff_dir.iterdir())
        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".json", ".yaml", ".yml"}
        and not p.name.startswith("interpreted-")
        and p.name != ".gitkeep"
    ]
    if not sources:
        raise FileNotFoundError(f"No handoff files in {handoff_dir}")

    source = sources[-1]
    interpreted = interpret_text(_read_text(source), filename=source.name)
    version = format_version(int(data.get("current_version") or 1))
    out = handoff_dir / f"interpreted-{version}.yaml"
    out.write_text(yaml.safe_dump(interpreted, sort_keys=False, allow_unicode=True), encoding="utf-8")
    rel = f"handoff/{source.name}"
    data["latest_handoff"] = rel
    save_project(data)
    interpreted["written"] = str(out)
    return interpreted


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interpret a project Design Handoff.")
    parser.add_argument("--project", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = interpret_project(args.project)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(yaml.safe_dump(result, sort_keys=False, allow_unicode=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
