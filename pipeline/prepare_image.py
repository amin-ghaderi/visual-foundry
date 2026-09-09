"""Plan and optionally run the local image-preparation engine."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

_PIPELINE = Path(__file__).resolve().parent
if str(_PIPELINE) not in sys.path:
    sys.path.insert(0, str(_PIPELINE))

from config import load_config
from paths import ROOT
from project import load_project, project_dir, save_project

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}


def _load_engine(name: str):
    path = ROOT / "image-preparation" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"engine_{name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load image engine module: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _first_image(folder: Path) -> Path | None:
    files = [p for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
    return files[0] if files else None


def inspect_image(path: Path) -> dict[str, Any]:
    with Image.open(path) as im:
        mode = im.mode
        width, height = im.size
        arr = np.array(im.convert("RGBA"))
    alpha = arr[:, :, 3]
    transparent = int((alpha < 8).sum())
    opaque = int((alpha >= 250).sum())
    has_cutout = transparent > 0 and opaque > 0
    return {
        "path": str(path),
        "width": width,
        "height": height,
        "mode": mode,
        "transparent_pixels": transparent,
        "opaque_pixels": opaque,
        "has_cutout": has_cutout,
    }


def plan_stages(info: dict[str, Any], cfg: dict[str, Any]) -> list[str]:
    stages: list[str] = []
    portrait = cfg.get("default_portrait") or {}
    pw = int(portrait.get("width") or 1080)
    ph = int(portrait.get("height") or 810)
    if not info["has_cutout"]:
        stages.append("background_removal_birefnet")
    if cfg.get("image_pipeline", {}).get("edge_refine", True):
        stages.append("edge_refine")
    subject_w, subject_h = info["width"], info["height"]
    upscale_ok = cfg.get("image_pipeline", {}).get("upscale_when_subject_smaller_than_portrait", True)
    if upscale_ok and (subject_w < pw or subject_h < ph):
        stages.append("upscale_2x")
    stages.append("compose_final_portrait")
    return stages


def existing_named(prepared: Path, name: str) -> Path | None:
    path = prepared / name
    return path if path.is_file() else None


def plan_project(project_id: str) -> dict[str, Any]:
    cfg = load_config()
    data = load_project(project_id)
    root = project_dir(project_id)
    original = _first_image(root / "input")
    if original is None:
        raise FileNotFoundError(f"No original image in {root / 'input'}")

    prepared = root / "prepared"
    info = inspect_image(original)
    birefnet = existing_named(prepared, "person-birefnet-v01.png")
    inspect_src = inspect_image(birefnet) if birefnet else info
    stages = plan_stages(inspect_src if birefnet else info, cfg)

    present = {
        "original": str(original.relative_to(root)),
        "birefnet": "prepared/person-birefnet-v01.png" if birefnet else "",
        "refined": "prepared/person-refined-v01.png"
        if existing_named(prepared, "person-refined-v01.png")
        else "",
        "upscaled": "prepared/person-upscaled-v01.png"
        if existing_named(prepared, "person-upscaled-v01.png")
        else "",
        "final": "prepared/person-final.png" if existing_named(prepared, "person-final.png") else "",
    }
    return {
        "project_id": project_id,
        "template": data.get("template"),
        "original": inspect_image(original),
        "cutout_inspected": inspect_src,
        "stages": stages,
        "existing": present,
        "notes": [
            "Original photograph will not be overwritten.",
            "BiRefNet runs in ComfyUI when background_removal_birefnet is required and no cutout exists.",
            "Upscale is skipped when the subject already fills the portrait plate.",
        ],
    }


def execute_plan(project_id: str) -> dict[str, Any]:
    cfg = load_config()
    root = project_dir(project_id)
    prepared = root / "prepared"
    prepared.mkdir(parents=True, exist_ok=True)
    reports = ROOT / "reports" / project_id
    reports.mkdir(parents=True, exist_ok=True)

    plan = plan_project(project_id)
    stages = list(plan["stages"])
    original = root / plan["existing"]["original"]
    birefnet = prepared / "person-birefnet-v01.png"
    refined = prepared / "person-refined-v01.png"
    upscaled = prepared / "person-upscaled-v01.png"
    final = prepared / "person-final.png"

    if "background_removal_birefnet" in stages and not birefnet.is_file():
        raise RuntimeError(
            "Background removal is required but person-birefnet-v01.png is missing. "
            "Run the BiRefNet workflow via Comfy MCP "
            f"({ROOT / 'image-preparation' / 'workflows' / 'birefnet.json'}) "
            "and save the cutout to prepared/person-birefnet-v01.png."
        )

    results: dict[str, Any] = {"project_id": project_id, "ran": []}

    if "edge_refine" in stages:
        src = birefnet if birefnet.is_file() else original
        engine = _load_engine("edge_refine")
        base = engine.load_rgba(src)
        out, stats = engine.refine(base)
        refined.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(out, "RGBA").save(refined, "PNG")
        gate = engine.validate(base, out)
        report = {"pipeline": "edge_refine", "stats": stats, **gate}
        (reports / "person-refined-v01.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if report.get("quality_gate") != "PASS":
            raise RuntimeError(f"edge refine failed: {report.get('failures')}")
        results["ran"].append("edge_refine")

    src_for_upscale = refined if refined.is_file() else birefnet if birefnet.is_file() else original
    if "upscale_2x" in stages:
        engine = _load_engine("upscale_2x")
        src = engine.load_rgba(src_for_upscale)
        model = ROOT / cfg["image_pipeline"]["model"]
        session = engine.make_session(engine.ensure_model(model))
        out = engine.upscale_rgba(src, session)
        Image.fromarray(out, "RGBA").save(upscaled, "PNG")
        results["ran"].append("upscale_2x")

    compose_input = upscaled if upscaled.is_file() else src_for_upscale
    if "compose_final_portrait" in stages:
        engine = _load_engine("final_portrait_asset")
        portrait = cfg.get("default_portrait") or {}
        report = engine.compose_final(
            compose_input,
            final,
            canvas_w=int(portrait.get("width") or 1080),
            canvas_h=int(portrait.get("height") or 810),
        )
        (reports / "person-final.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        if report.get("quality_gate") != "PASS":
            raise RuntimeError(f"final compose failed: {report.get('quality_gate_failures')}")
        results["ran"].append("compose_final_portrait")

    data = load_project(project_id)
    data["latest_asset"] = "prepared/person-final.png"
    if data.get("status") == "draft":
        data["status"] = "assets-ready"
    save_project(data)
    results["latest_asset"] = data["latest_asset"]
    results["quality_gate"] = "PASS"
    return results


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or run image preparation for a project.")
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run local stages. Never overwrites input/. Does not call ComfyUI.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.execute:
            result = execute_plan(args.project)
        else:
            result = plan_project(args.project)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
