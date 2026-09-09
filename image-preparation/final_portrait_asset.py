"""Final 1080×810 portrait master for the Memorial Design Pipeline.

Geometric composition only: 1:1 copy of the validated 2× RGBA cutout onto a
transparent canvas. No upscale, no generation, no retouch, no distortion.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smart_portrait_crop import (  # noqa: E402
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    copy_window,
    destination_origin,
    expand_bbox,
    source_window,
    subject_bbox,
    _load_rgba,
)

PIPELINE = "MEMORIAL_PORTRAIT_PREP_V1_4"


def validate_final(
    src: np.ndarray,
    out: np.ndarray,
    window: tuple[int, int, int, int],
    dest_xy: tuple[int, int],
    bbox: tuple[int, int, int, int],
    canvas_w: int,
    canvas_h: int,
) -> dict:
    sx0, sy0, sx1, sy1 = window
    dx, dy = dest_xy
    win_w, win_h = sx1 - sx0, sy1 - sy0
    copied = src[sy0:sy1, sx0:sx1]
    placed = out[dy : dy + win_h, dx : dx + win_w]

    pixels_equal = bool(np.array_equal(copied, placed))
    generated_pixels = 0
    modified_source_pixels = 0 if pixels_equal else int(np.any(copied != placed, axis=2).sum())
    distortion = False
    aspect_ratio_changed = False

    bbox_w, bbox_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    complete_subject = win_w == bbox_w and win_h == bbox_h
    head_clipped = sy0 > bbox[1] or not complete_subject
    shoulders_lost = not complete_subject
    clothing_lost = not complete_subject

    has_alpha = out.shape[2] == 4
    dims_ok = out.shape[0] == canvas_h and out.shape[1] == canvas_w
    left = dx
    right = canvas_w - dx - win_w
    professionally_centered = abs(left - right) <= 1

    # Destination outside the copied window must stay fully transparent.
    mask = np.ones((canvas_h, canvas_w), dtype=bool)
    mask[dy : dy + win_h, dx : dx + win_w] = False
    outside_clean = bool(np.all(out[mask] == 0))

    failures: list[str] = []
    if not dims_ok:
        failures.append(f"dimensions are {out.shape[1]}x{out.shape[0]}, expected {canvas_w}x{canvas_h}")
    if not has_alpha:
        failures.append("alpha channel is missing")
    if not complete_subject:
        failures.append("subject does not fit at 1:1; cropping is not allowed for the final asset")
    if head_clipped:
        failures.append("head is clipped")
    if shoulders_lost or clothing_lost:
        failures.append("shoulders or clothing were cropped")
    if not pixels_equal or modified_source_pixels != 0:
        failures.append("source pixels were modified")
    if generated_pixels != 0:
        failures.append("generated pixels are present")
    if distortion or aspect_ratio_changed:
        failures.append("distortion or aspect-ratio change detected")
    if not professionally_centered:
        failures.append(f"horizontal centering is uneven (left {left}, right {right})")
    if not outside_clean:
        failures.append("pixels exist outside the copied source window")

    return {
        "pixels_copied_unchanged": int(copied.size // 4),
        "modified_source_pixels": modified_source_pixels,
        "generated_pixels": generated_pixels,
        "distortion": distortion,
        "aspect_ratio_changed": aspect_ratio_changed,
        "complete_subject_copied": complete_subject,
        "head_clipped": head_clipped,
        "shoulders_lost": shoulders_lost,
        "professionally_centered": professionally_centered,
        "has_alpha": has_alpha,
        "dimensions_ok": dims_ok,
        "failures": failures,
        "quality_gate": "FAIL" if failures else "PASS",
    }


def compose_final(
    input_path: Path,
    output_path: Path,
    canvas_w: int = DEFAULT_WIDTH,
    canvas_h: int = DEFAULT_HEIGHT,
) -> dict:
    src = _load_rgba(input_path)
    src_h, src_w = src.shape[:2]
    bbox = expand_bbox(subject_bbox(src[:, :, 3]), src_w, src_h)
    window = source_window(bbox, canvas_w, canvas_h)
    sx0, sy0, sx1, sy1 = window
    win_w, win_h = sx1 - sx0, sy1 - sy0
    dest_xy = destination_origin(win_w, win_h, canvas_w, canvas_h)
    dx, dy = dest_xy

    out = copy_window(src, window, canvas_w, canvas_h, dest_xy)
    gate = validate_final(src, out, window, dest_xy, bbox, canvas_w, canvas_h)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGBA").save(output_path, "PNG")

    occupancy = int((out[:, :, 3] > 0).sum()) / float(canvas_w * canvas_h)

    return {
        "pipeline": PIPELINE,
        "input": str(input_path),
        "output": str(output_path),
        "input_dimensions": [src_w, src_h],
        "output_dimensions": [int(out.shape[1]), int(out.shape[0])],
        "subject_bounding_box": {
            "x0": bbox[0],
            "y0": bbox[1],
            "x1": bbox[2],
            "y1": bbox[3],
            "width": bbox[2] - bbox[0],
            "height": bbox[3] - bbox[1],
        },
        "subject_position": {"x": dx, "y": dy, "width": win_w, "height": win_h},
        "margins": {
            "top": dy,
            "left": dx,
            "right": canvas_w - dx - win_w,
            "bottom": canvas_h - dy - win_h,
        },
        "percentage_of_canvas_occupied_by_subject": round(occupancy * 100.0, 4),
        "number_of_source_pixels_copied": gate["pixels_copied_unchanged"],
        "number_of_generated_pixels": gate["generated_pixels"],
        "number_of_modified_source_pixels": gate["modified_source_pixels"],
        "aspect_ratio_changed": "YES" if gate["aspect_ratio_changed"] else "NO",
        "distortion_occurred": "NO" if not gate["distortion"] else "YES",
        "source_pixels_modified": "NO" if gate["modified_source_pixels"] == 0 else "YES",
        "alpha_preserved": "YES" if gate["has_alpha"] else "NO",
        "complete_subject_copied": gate["complete_subject_copied"],
        "quality_gate": gate["quality_gate"],
        "quality_gate_failures": gate["failures"],
        "notes": [
            "Geometric 1:1 copy of the validated 2× Real-ESRGAN cutout onto a transparent 1080×810 canvas.",
            "No second upscale, no generation, no face retouch.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose the final 1080×810 memorial portrait asset.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("projects/P001/prepared/person-upscaled-v01.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/P001/prepared/person-final.png"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/P001/person-final.json"),
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(f"Required 2× input not found: {args.input}")
    report = compose_final(args.input, args.output, args.width, args.height)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report.get("quality_gate") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
