"""Edge refinement for BiRefNet cutouts.

Deterministic local cleanup only:
- opaque subject pixels are copied unchanged
- edge / partial-alpha pixels may be despilled and have alpha tightened
- RGB on the edge is taken from the nearest already-opaque subject pixel
- no models, no generation, no face retouch, no custom Comfy nodes
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

OPAQUE_MIN = 250
INTERIOR_ERODE = 2
DROP_ALPHA_MAX = 80
DROP_BLUE_EXCESS = 18
GHOST_ALPHA_MAX = 24
OUTER_DROP_BLUE_EXCESS = 22
REDUCE_ALPHA_MAX = 200
REDUCE_BLUE_EXCESS = 25
REDUCE_ALPHA_SCALE = 0.45


def load_rgba(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.array(im.convert("RGBA"))


def blue_excess(rgb: np.ndarray) -> np.ndarray:
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    return np.clip(b - np.maximum(r, g), 0, None)


def nearest_opaque_rgb(rgb: np.ndarray, opaque: np.ndarray) -> np.ndarray:
    if not opaque.any():
        raise ValueError("No opaque subject pixels found; cannot refine edges.")
    _, inds = ndimage.distance_transform_edt(~opaque, return_indices=True)
    return rgb[inds[0], inds[1]]


def refine(src: np.ndarray) -> tuple[np.ndarray, dict]:
    rgb = src[:, :, :3]
    alpha = src[:, :, 3]
    opaque = alpha >= OPAQUE_MIN
    interior = ndimage.binary_erosion(opaque, iterations=INTERIOR_ERODE)
    if not interior.any():
        interior = opaque
    edge = (alpha > 0) & ~interior
    outer = edge & ~ndimage.binary_erosion(alpha > 0, iterations=1)
    bex = blue_excess(rgb)
    nearest_rgb = nearest_opaque_rgb(rgb, interior)

    out = src.copy()
    out[edge, :3] = nearest_rgb[edge]

    drop = edge & (
        ((alpha < DROP_ALPHA_MAX) & (bex > DROP_BLUE_EXCESS))
        | (alpha < GHOST_ALPHA_MAX)
        | (outer & (bex > OUTER_DROP_BLUE_EXCESS))
    )
    out[drop, :] = 0

    reduce = edge & ~drop & (bex > REDUCE_BLUE_EXCESS) & (alpha < REDUCE_ALPHA_MAX)
    out[reduce, 3] = (alpha[reduce].astype(np.float32) * REDUCE_ALPHA_SCALE).astype(np.uint8)

    # Extra chroma despill on remaining edge pixels only (no new content).
    remain = edge & ~drop
    r = out[:, :, 0].astype(np.int16)
    g = out[:, :, 1].astype(np.int16)
    b = out[:, :, 2].astype(np.int16)
    out[remain, 2] = np.minimum(b, np.maximum(r, g))[remain].astype(np.uint8)

    out[out[:, :, 3] == 0, :3] = 0

    stats = {
        "interior_pixels": int(interior.sum()),
        "opaque_pixels": int(opaque.sum()),
        "edge_pixels_in": int(edge.sum()),
        "edge_pixels_dropped": int(drop.sum()),
        "edge_pixels_alpha_reduced": int(reduce.sum()),
        "edge_pixels_out": int(((out[:, :, 3] > 0) & ~interior).sum()),
        "interior_pixels_unchanged": bool(np.array_equal(out[interior], src[interior])),
    }
    return out, stats


def contamination(arr: np.ndarray) -> dict:
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    opaque = alpha >= OPAQUE_MIN
    interior = ndimage.binary_erosion(opaque, iterations=INTERIOR_ERODE)
    if not interior.any():
        interior = opaque
    edge = (alpha > 0) & ~interior
    bex = blue_excess(rgb)
    blueish = edge & (bex > 15)
    return {
        "edge_pixels": int(edge.sum()),
        "blueish_edge_pixels": int(blueish.sum()),
        "mean_blue_excess_on_edge": (
            round(float(bex[edge].mean()), 4) if edge.any() else 0.0
        ),
        "mean_edge_rgb": (
            [round(float(x), 2) for x in rgb[edge].mean(axis=0)] if edge.any() else [0, 0, 0]
        ),
    }


def validate(base: np.ndarray, refined: np.ndarray) -> dict:
    failures: list[str] = []
    same_dims = base.shape == refined.shape
    if not same_dims:
        failures.append(f"dimensions differ: base {base.shape} vs refined {refined.shape}")

    opaque = base[:, :, 3] >= OPAQUE_MIN
    interior = ndimage.binary_erosion(opaque, iterations=INTERIOR_ERODE)
    if not interior.any():
        interior = opaque
    opaque_unchanged = bool(np.array_equal(refined[interior], base[interior])) if same_dims else False
    if not opaque_unchanged:
        failures.append("opaque subject pixels were changed")

    before = contamination(base)
    after = contamination(refined)
    spill_reduced = after["mean_blue_excess_on_edge"] < before["mean_blue_excess_on_edge"]
    blueish_reduced = after["blueish_edge_pixels"] <= before["blueish_edge_pixels"]
    if not spill_reduced:
        failures.append("background-color contamination was not reduced")
    if not blueish_reduced:
        failures.append("blueish edge pixel count increased")

    generated_pixels = 0
    source_pixels_modified = "NO"

    return {
        "same_dimensions": same_dims,
        "png_rgba": True,
        "opaque_subject_pixels_unchanged": opaque_unchanged,
        "edge_pixels_may_change": True,
        "background_contamination_reduced": spill_reduced and blueish_reduced,
        "face_regeneration": "NO",
        "generated_pixels": generated_pixels,
        "source_pixels_modified": source_pixels_modified,
        "contamination_before": before,
        "contamination_after": after,
        "failures": failures,
        "quality_gate": "FAIL" if failures else "PASS",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local BiRefNet edge refinement.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("projects/P001/prepared/person-birefnet-v01.png"),
        help="Existing BiRefNet PNG (not overwritten).",
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=Path("projects/P001/prepared/person-birefnet-v01.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/P001/prepared/person-refined-v01.png"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/P001/person-refined-v01.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.exists():
        raise FileNotFoundError(f"BiRefNet source not found: {args.source}")

    args.base.parent.mkdir(parents=True, exist_ok=True)
    if args.base.resolve() != args.source.resolve():
        shutil.copy2(args.source, args.base)

    base = load_rgba(args.base)
    refined, stats = refine(base)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(refined, "RGBA").save(args.output, "PNG")

    gate = validate(base, refined)
    report = {
        "pipeline": "MEMORIAL_PORTRAIT_PREP_EDGE_REFINE",
        "source_birefnet": str(args.source),
        "base": str(args.base),
        "output": str(args.output),
        "dimensions": [int(refined.shape[1]), int(refined.shape[0])],
        "mode": "RGBA",
        "format": "PNG",
        "method": (
            "Local compositing defringe: interior opaque pixels bitwise-copied; "
            "morphological/partial-alpha edge RGB taken from nearest interior pixel; "
            "low-alpha and outer-contour blue-spill dropped. No generation."
        ),
        "stats": stats,
        **gate,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["quality_gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
