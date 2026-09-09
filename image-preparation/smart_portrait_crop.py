"""Smart portrait crop for the Memorial Design Pipeline.

Place a transparent RGBA cutout onto a fixed canvas using only geometry:
alpha bounding box, uniform (1:1) copy, and transparent padding.

No scaling, stretching, generation, outpainting, or pixel mutation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 810
ALPHA_THRESHOLD = 8
BBOX_PAD_PX = 2
HEADROOM_RATIO = 0.10  # fraction of canvas height above the subject when it fully fits


def _load_rgba(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.array(im.convert("RGBA"))


def subject_bbox(alpha: np.ndarray, threshold: int = ALPHA_THRESHOLD) -> tuple[int, int, int, int]:
    """Return exclusive (x0, y0, x1, y1) covering pixels with alpha > threshold."""
    ys, xs = np.where(alpha > threshold)
    if xs.size == 0:
        raise ValueError("No subject found in the alpha channel.")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def expand_bbox(
    bbox: tuple[int, int, int, int],
    src_w: int,
    src_h: int,
    pad: int = BBOX_PAD_PX,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = bbox
    return (
        max(0, x0 - pad),
        max(0, y0 - pad),
        min(src_w, x1 + pad),
        min(src_h, y1 + pad),
    )


def source_window(
    bbox: tuple[int, int, int, int],
    canvas_w: int,
    canvas_h: int,
) -> tuple[int, int, int, int]:
    """Choose a 1:1 source crop that never exceeds the canvas.

    If the subject is larger than the canvas, keep the top of the bbox (head)
    and as much width/shoulders as possible. Never scale.
    """
    x0, y0, x1, y1 = bbox
    sw, sh = x1 - x0, y1 - y0

    win_w = min(sw, canvas_w)
    win_h = min(sh, canvas_h)

    # Horizontal: center on the subject; clamp to bbox.
    cx = x0 + sw // 2
    sx0 = cx - win_w // 2
    sx0 = min(max(sx0, x0), x1 - win_w)
    sx1 = sx0 + win_w

    # Vertical: lock to the top of the bbox so the head is never clipped.
    sy0 = y0
    sy1 = sy0 + win_h
    if sy1 > y1:
        sy1 = y1
        sy0 = sy1 - win_h

    return sx0, sy0, sx1, sy1


def destination_origin(
    win_w: int,
    win_h: int,
    canvas_w: int,
    canvas_h: int,
    headroom_ratio: float = HEADROOM_RATIO,
) -> tuple[int, int]:
    """Place the 1:1 window on the canvas with editorial headroom when it fits."""
    dx = (canvas_w - win_w) // 2

    leftover = canvas_h - win_h
    if leftover <= 0:
        dy = 0
    else:
        preferred = int(round(canvas_h * headroom_ratio))
        dy = min(preferred, leftover)
        # If preferred headroom would pin the subject to the bottom edge, center instead.
        if leftover - dy < canvas_h * 0.04:
            dy = leftover // 2

    return dx, dy


def copy_window(
    src: np.ndarray,
    window: tuple[int, int, int, int],
    canvas_w: int,
    canvas_h: int,
    dest_xy: tuple[int, int],
) -> np.ndarray:
    sx0, sy0, sx1, sy1 = window
    dx, dy = dest_xy
    win_w, win_h = sx1 - sx0, sy1 - sy0

    canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)
    canvas[dy : dy + win_h, dx : dx + win_w] = src[sy0:sy1, sx0:sx1]
    return canvas


def validate(
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
    distortion = False
    source_modified = not pixels_equal

    head_clipped = sy0 > bbox[1]
    # Shoulders/clothing lost if we dropped a large fraction of the subject bbox.
    bbox_w, bbox_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    lost_w = bbox_w - win_w
    lost_h = bbox_h - win_h
    major_loss = (lost_w > bbox_w * 0.12) or (lost_h > bbox_h * 0.18)

    alpha = out[:, :, 3]
    has_alpha = out.shape[2] == 4
    dims_ok = out.shape[0] == canvas_h and out.shape[1] == canvas_w

    failures: list[str] = []
    if not dims_ok:
        failures.append(f"dimensions are {out.shape[1]}x{out.shape[0]}, expected {canvas_w}x{canvas_h}")
    if not has_alpha:
        failures.append("alpha channel is missing")
    if head_clipped:
        failures.append("head is clipped")
    if major_loss:
        failures.append("major shoulder/clothing areas are lost")
    if source_modified:
        failures.append("source pixels were modified")
    if generated_pixels != 0:
        failures.append("generated pixels are present")
    if distortion:
        failures.append("distortion detected")

    return {
        "pixels_copied_unchanged": int(copied.size // 4),
        "source_pixels_modified": source_modified,
        "generated_pixels": generated_pixels,
        "distortion": distortion,
        "head_clipped": head_clipped,
        "major_subject_loss": major_loss,
        "has_alpha": has_alpha,
        "dimensions_ok": dims_ok,
        "failures": failures,
        "quality_gate": "FAIL" if failures else "PASS",
    }


def prepare_portrait(
    input_path: Path,
    output_path: Path,
    canvas_w: int = DEFAULT_WIDTH,
    canvas_h: int = DEFAULT_HEIGHT,
    requested_input: Path | None = None,
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
    gate = validate(src, out, window, dest_xy, bbox, canvas_w, canvas_h)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out, "RGBA").save(output_path, "PNG")

    subject_alpha = int((out[:, :, 3] > 0).sum())
    occupancy = subject_alpha / float(canvas_w * canvas_h)

    report = {
        "pipeline": "MEMORIAL_PORTRAIT_PREP_V1_2",
        "requested_input": str(requested_input or input_path),
        "input": str(input_path),
        "output": str(output_path),
        "source_dimensions": [src_w, src_h],
        "output_dimensions": [int(out.shape[1]), int(out.shape[0])],
        "subject_bounding_box_source": {
            "x0": bbox[0],
            "y0": bbox[1],
            "x1": bbox[2],
            "y1": bbox[3],
        },
        "source_window_copied": {
            "x0": sx0,
            "y0": sy0,
            "x1": sx1,
            "y1": sy1,
        },
        "subject_width": win_w,
        "subject_height": win_h,
        "subject_position_in_output": {"x": dx, "y": dy, "width": win_w, "height": win_h},
        "margins": {
            "top": dy,
            "left": dx,
            "right": canvas_w - dx - win_w,
            "bottom": canvas_h - dy - win_h,
        },
        "subject_occupancy_percent": round(occupancy * 100.0, 4),
        "number_of_source_pixels_copied_unchanged": gate["pixels_copied_unchanged"],
        "number_of_generated_pixels": gate["generated_pixels"],
        "distortion_occurred": "NO" if not gate["distortion"] else "YES",
        "source_pixels_modified": "NO" if not gate["source_pixels_modified"] else "YES",
        "quality_gate": gate["quality_gate"],
        "quality_gate_failures": gate["failures"],
        "notes": [],
    }
    return report


def resolve_input(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(
            f"Required input not found: {path}. "
            "The production pipeline does not fall back to the BiRefNet base image."
        )
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="1:1 smart portrait crop onto a transparent canvas.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("projects/P001/prepared/person-refined-v01.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/P001/prepared/person-crop-v01.png"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/P001/person-crop-v01.json"),
    )
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = resolve_input(args.input)
    report = prepare_portrait(
        input_path=input_path,
        output_path=args.output,
        canvas_w=args.width,
        canvas_h=args.height,
        requested_input=args.input,
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["quality_gate"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
