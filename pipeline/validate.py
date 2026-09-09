"""Validate repository structure, CLI, a project, and the image engine."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

_PIPELINE = Path(__file__).resolve().parent
if str(_PIPELINE) not in sys.path:
    sys.path.insert(0, str(_PIPELINE))

from config import load_config
from paths import ROOT
from project import format_version, load_project, project_dir, templates_dir

P001_ORIGINAL_SHA256 = "16C01E49020258D534C0C24A960CF83DA3EED607B171B062061E1819B0B25EFE"
P001_FINAL_SHA256 = "64747C1E99D114DD8D66BFA9EDF1C5D54D039AD453886091B7F73C83E36AFA7E"
ENGINE_MODULES = (
    "edge_refine",
    "smart_portrait_crop",
    "upscale_2x",
    "final_portrait_asset",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _ok(item: str, detail: str = "") -> dict[str, str]:
    return {"item": item, "result": "PASS", "detail": detail}


def _fail(item: str, detail: str) -> dict[str, str]:
    return {"item": item, "result": "FAIL", "detail": detail}


def validate_structure() -> list[dict[str, str]]:
    required = [
        ROOT / "README.md",
        ROOT / "DESIGN_PROTOCOL.md",
        ROOT / "CURSOR_AGENT.md",
        ROOT / "DESIGN_HANDOFF_PROTOCOL.md",
        ROOT / "config.yaml",
        ROOT / "pipeline" / "run.py",
        ROOT / "pipeline" / "create_project.py",
        ROOT / "pipeline" / "prepare_image.py",
        ROOT / "pipeline" / "version.py",
        ROOT / "pipeline" / "validate.py",
        ROOT / "pipeline" / "export.py",
        ROOT / "templates" / "memorial" / "MASTER.md",
        ROOT / "templates" / "memorial" / "DESIGN_SPEC.md",
        ROOT / "templates" / "memorial" / "PERSON_SCHEMA.json",
        ROOT / "image-preparation" / "edge_refine.py",
        ROOT / "image-preparation" / "models" / "RealESRGAN_x2plus.onnx",
        ROOT / "archive" / "legacy",
        ROOT / "reports",
        ROOT / "projects",
    ]
    checks = []
    for path in required:
        if path.exists():
            checks.append(_ok(f"exists:{path.relative_to(ROOT)}"))
        else:
            checks.append(_fail(f"exists:{path.relative_to(ROOT)}", "missing"))
    return checks


def validate_config() -> list[dict[str, str]]:
    checks = []
    try:
        cfg = load_config()
        checks.append(_ok("config.yaml", f"project_name={cfg.get('project_name')}"))
        for key in ("projects", "templates", "archive", "reports", "image_engine", "models"):
            if key in cfg.get("paths", {}):
                checks.append(_ok(f"config.paths.{key}", str(cfg["paths"][key])))
            else:
                checks.append(_fail(f"config.paths.{key}", "missing"))
    except Exception as exc:
        checks.append(_fail("config.yaml", str(exc)))
    return checks


def validate_imports() -> list[dict[str, str]]:
    checks = []
    for name in ENGINE_MODULES:
        path = ROOT / "image-preparation" / f"{name}.py"
        try:
            spec = importlib.util.spec_from_file_location(f"chk_{name}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            checks.append(_ok(f"import:{name}"))
        except Exception as exc:
            checks.append(_fail(f"import:{name}", str(exc)))
    for name in ("project", "create_project", "prepare_image", "handoff", "export", "version"):
        try:
            spec = importlib.util.spec_from_file_location(
                f"chk_pipeline_{name}", ROOT / "pipeline" / f"{name}.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            checks.append(_ok(f"import:pipeline.{name}"))
        except Exception as exc:
            checks.append(_fail(f"import:pipeline.{name}", str(exc)))
    return checks


def validate_cli() -> list[dict[str, str]]:
    cmd = [sys.executable, str(ROOT / "pipeline" / "run.py"), "--help"]
    try:
        completed = subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=str(ROOT))
        if completed.returncode == 0 and "create-project" in completed.stdout:
            return [_ok("cli:run.py --help")]
        return [_fail("cli:run.py --help", completed.stderr or completed.stdout)]
    except Exception as exc:
        return [_fail("cli:run.py --help", str(exc))]


def validate_templates() -> list[dict[str, str]]:
    root = templates_dir() / "memorial"
    checks = []
    if root.is_dir():
        checks.append(_ok("template:memorial", str(root.relative_to(ROOT))))
    else:
        checks.append(_fail("template:memorial", "missing"))
    schema = root / "PERSON_SCHEMA.json"
    if schema.is_file():
        try:
            json.loads(schema.read_text(encoding="utf-8"))
            checks.append(_ok("template:PERSON_SCHEMA.json"))
        except json.JSONDecodeError as exc:
            checks.append(_fail("template:PERSON_SCHEMA.json", str(exc)))
    else:
        checks.append(_fail("template:PERSON_SCHEMA.json", "missing"))
    return checks


def validate_create_project_sandbox() -> list[dict[str, str]]:
    from project import next_project_id, used_project_ids

    try:
        used = used_project_ids()
        nxt = next_project_id()
        if nxt in used:
            return [_fail("create-project:next-id", f"{nxt} already used")]
        return [_ok("create-project:next-id", f"next={nxt} used={sorted(used)}")]
    except Exception as exc:
        return [_fail("create-project:next-id", str(exc))]


def validate_project(project_id: str) -> list[dict[str, str]]:
    checks = []
    try:
        data = load_project(project_id)
        checks.append(_ok(f"{project_id}:project.yaml", f"version={format_version(int(data.get('current_version') or 1))}"))
    except Exception as exc:
        return [_fail(f"{project_id}:project.yaml", str(exc))]

    root = project_dir(project_id)
    for name in ("input", "prepared", "handoff", "figma", "exports", "versions"):
        path = root / name
        if path.is_dir():
            checks.append(_ok(f"{project_id}:{name}/"))
        else:
            checks.append(_fail(f"{project_id}:{name}/", "missing"))

    original = root / "input" / "person-original.png"
    final = root / "prepared" / "person-final.png"
    if original.is_file():
        digest = sha256_file(original)
        if project_id == "P001" and digest != P001_ORIGINAL_SHA256:
            checks.append(_fail("P001:original-hash", digest))
        else:
            checks.append(_ok(f"{project_id}:original", digest[:16]))
    else:
        checks.append(_fail(f"{project_id}:original", "missing"))

    if final.is_file():
        digest = sha256_file(final)
        if project_id == "P001" and digest != P001_FINAL_SHA256:
            checks.append(_fail("P001:final-hash", digest))
        else:
            checks.append(_ok(f"{project_id}:final", digest[:16]))
        try:
            from PIL import Image

            with Image.open(final) as im:
                if im.size == (1080, 810) and im.mode in {"RGBA", "RGB"}:
                    checks.append(_ok(f"{project_id}:final-size", f"{im.size} {im.mode}"))
                else:
                    checks.append(_fail(f"{project_id}:final-size", f"{im.size} {im.mode}"))
        except Exception as exc:
            checks.append(_fail(f"{project_id}:final-size", str(exc)))
    else:
        checks.append(_fail(f"{project_id}:final", "missing"))
    return checks


def run_validation(project_id: str | None) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    checks.extend(validate_structure())
    checks.extend(validate_config())
    checks.extend(validate_imports())
    checks.extend(validate_cli())
    checks.extend(validate_templates())
    checks.extend(validate_create_project_sandbox())
    if project_id:
        checks.extend(validate_project(project_id))

    model = ROOT / "image-preparation" / "models" / "RealESRGAN_x2plus.onnx"
    if model.is_file() and model.stat().st_size > 1_000_000:
        checks.append(_ok("model:RealESRGAN_x2plus.onnx", str(model.stat().st_size)))
    else:
        checks.append(_fail("model:RealESRGAN_x2plus.onnx", "missing or too small"))

    failed = [c for c in checks if c["result"] != "PASS"]
    report = {
        "status": "FAIL" if failed else "PASS",
        "failed": len(failed),
        "passed": len(checks) - len(failed),
        "checks": checks,
        "mcp": {
            "figma": "checked separately via Figma MCP whoami",
            "comfy": "checked separately via Comfy MCP server_info",
        },
    }
    out_dir = ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if project_id:
        proj_dir = out_dir / project_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "validate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate pipeline structure and an optional project.")
    parser.add_argument("--project", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = run_validation(args.project)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
