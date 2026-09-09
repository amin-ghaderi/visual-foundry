"""2x non-generative upscale for Memorial Design Pipeline portraits.

RGB is super-resolved with a local Real-ESRGAN x2 ONNX model (CPU, tiled).
Alpha is resized with Lanczos so the existing silhouette is not invented.

No face restoration, no generative models, no cloud inference.
"""

from __future__ import annotations

import argparse
import json
import time
import traceback
import urllib.request
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

SCALE = 2
OPAQUE_MIN = 250
TILE = 512
TILE_OVERLAP = 16
EXPECTED_SIZE = None  # optional WxH; set via --expect-size for a specific benchmark
MODEL_URL = (
    "https://huggingface.co/huggingworld/onnx-image-models/resolve/main/"
    "2x-realesrgan-x2plus.onnx"
)
MIN_MODEL_BYTES = 1_000_000
IDENTITY_MAE_MAX = 12.0
SILHOUETTE_IOU_MIN = 0.98
DETAIL_RATIO_MIN = 1.0


def load_rgba(path: Path) -> np.ndarray:
    with Image.open(path) as im:
        return np.array(im.convert("RGBA"))


def ensure_model(model_path: Path) -> Path:
    if model_path.exists() and model_path.stat().st_size >= MIN_MODEL_BYTES:
        return model_path
    model_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Real-ESRGAN x2 ONNX to {model_path} ...")
    req = urllib.request.Request(MODEL_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, model_path.open("wb") as out:
        while True:
            chunk = resp.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
    if model_path.stat().st_size < MIN_MODEL_BYTES:
        raise RuntimeError(
            f"Model download looks invalid ({model_path.stat().st_size} bytes)."
        )
    return model_path


def make_session(model_path: Path) -> ort.InferenceSession:
    so = ort.SessionOptions()
    so.enable_mem_pattern = True
    so.intra_op_num_threads = 4
    so.inter_op_num_threads = 1
    return ort.InferenceSession(
        str(model_path),
        sess_options=so,
        providers=["CPUExecutionProvider"],
    )


def _infer_nchw(session: ort.InferenceSession, tile_rgb: np.ndarray) -> np.ndarray:
    inp = session.get_inputs()[0]
    x = np.transpose(tile_rgb.astype(np.float32) / 255.0, (2, 0, 1))[None]
    y = session.run(None, {inp.name: x})[0][0]
    if y.shape[0] in (1, 3):
        y = np.transpose(y, (1, 2, 0))
    return np.clip(y, 0.0, 1.0)


def _tile_weights(h: int, w: int, overlap: int) -> np.ndarray:
    wy = np.ones(h, dtype=np.float32)
    wx = np.ones(w, dtype=np.float32)
    ov_y = min(overlap, max(1, h // 4))
    ov_x = min(overlap, max(1, w // 4))
    if ov_y > 1:
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, ov_y, dtype=np.float32))
        wy[:ov_y] *= ramp
        wy[-ov_y:] *= ramp[::-1]
    if ov_x > 1:
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, ov_x, dtype=np.float32))
        wx[:ov_x] *= ramp
        wx[-ov_x:] *= ramp[::-1]
    return wy[:, None] * wx[None, :]


def pad_to_multiple(rgb: np.ndarray, multiple: int = 4) -> tuple[np.ndarray, tuple[int, int]]:
    h, w = rgb.shape[:2]
    ph = (multiple - h % multiple) % multiple
    pw = (multiple - w % multiple) % multiple
    if ph == 0 and pw == 0:
        return rgb, (0, 0)
    padded = np.pad(rgb, ((0, ph), (0, pw), (0, 0)), mode="reflect")
    return padded, (ph, pw)


def upscale_rgb_tiled(
    session: ort.InferenceSession,
    rgb: np.ndarray,
    scale: int = SCALE,
    tile: int = TILE,
    overlap: int = TILE_OVERLAP,
) -> np.ndarray:
    h, w = rgb.shape[:2]
    padded, (ph, pw) = pad_to_multiple(rgb, 4)
    hp, wp = padded.shape[:2]
    if hp <= tile and wp <= tile:
        pred = _infer_nchw(session, padded)
        pred = pred[: h * scale, : w * scale]
        return np.clip(np.round(pred * 255.0), 0, 255).astype(np.uint8)

    out_h, out_w = h * scale, w * scale
    acc = np.zeros((out_h, out_w, 3), dtype=np.float32)
    weight = np.zeros((out_h, out_w, 1), dtype=np.float32)
    step = max(1, tile - overlap)

    ys = list(range(0, max(1, h - tile + 1), step))
    xs = list(range(0, max(1, w - tile + 1), step))
    if ys[-1] != h - tile:
        ys.append(max(0, h - tile))
    if xs[-1] != w - tile:
        xs.append(max(0, w - tile))

    for y0 in ys:
        y1 = min(h, y0 + tile)
        for x0 in xs:
            x1 = min(w, x0 + tile)
            patch = rgb[y0:y1, x0:x1]
            ph, pw = patch.shape[:2]
            padded_patch, _ = pad_to_multiple(patch, 4)
            pred = _infer_nchw(session, padded_patch)[: ph * scale, : pw * scale]
            ww = _tile_weights(pred.shape[0], pred.shape[1], overlap * scale)
            oy0, ox0 = y0 * scale, x0 * scale
            oy1, ox1 = oy0 + pred.shape[0], ox0 + pred.shape[1]
            acc[oy0:oy1, ox0:ox1] += pred * ww[..., None]
            weight[oy0:oy1, ox0:ox1] += ww[..., None]

    acc = acc / np.maximum(weight, 1e-6)
    return np.clip(np.round(acc * 255.0), 0, 255).astype(np.uint8)


def lanczos_resize(arr: np.ndarray, size: tuple[int, int], mode: str) -> np.ndarray:
    return np.array(Image.fromarray(arr, mode=mode).resize(size, Image.Resampling.LANCZOS))


def box_downscale(rgb: np.ndarray, scale: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    nh, nw = h // scale, w // scale
    cropped = rgb[: nh * scale, : nw * scale]
    return cropped.reshape(nh, scale, nw, scale, -1).mean(axis=(1, 3))


def silhouette_iou(a: np.ndarray, b: np.ndarray, thr: int = 8) -> float:
    ma = a > thr
    mb = b > thr
    inter = np.logical_and(ma, mb).sum()
    union = np.logical_or(ma, mb).sum()
    return float(inter / union) if union else 1.0


def laplacian_var(rgb: np.ndarray, mask: np.ndarray) -> float:
    img = rgb.astype(np.float32)
    gray = 0.299 * img[:, :, 0] + 0.587 * img[:, :, 1] + 0.114 * img[:, :, 2]
    lap = (
        gray[1:-1, 1:-1] * 4.0
        - gray[:-2, 1:-1]
        - gray[2:, 1:-1]
        - gray[1:-1, :-2]
        - gray[1:-1, 2:]
    )
    m = mask[1:-1, 1:-1]
    if not m.any():
        return 0.0
    return float(lap[m].var())


def upscale_rgba(src: np.ndarray, session: ort.InferenceSession, tile: int = TILE) -> np.ndarray:
    rgb = src[:, :, :3]
    alpha = src[:, :, 3]
    h, w = alpha.shape
    out_size = (w * SCALE, h * SCALE)
    rgb_2x = upscale_rgb_tiled(session, rgb, tile=tile)
    alpha_2x = lanczos_resize(alpha, out_size, "L")
    rgb_2x[alpha_2x == 0] = 0
    return np.dstack([rgb_2x, alpha_2x])


def validate(src: np.ndarray, out: np.ndarray, lanczos: np.ndarray, elapsed_s: float, oom: bool) -> dict:
    failures: list[str] = []
    src_h, src_w = src.shape[:2]
    out_h, out_w = out.shape[:2]
    expected_w, expected_h = src_w * SCALE, src_h * SCALE
    dims_ok = (out_w, out_h) == (expected_w, expected_h)
    if not dims_ok:
        failures.append(f"dimensions are {out_w}x{out_h}, expected {expected_w}x{expected_h}")

    alpha_preserved = out.shape[2] == 4 and src.shape[2] == 4
    if not alpha_preserved:
        failures.append("alpha channel missing")

    src_alpha_2x = lanczos_resize(src[:, :, 3], (expected_w, expected_h), "L")
    iou = silhouette_iou(src_alpha_2x, out[:, :, 3]) if alpha_preserved else 0.0
    geometry_changed = iou < SILHOUETTE_IOU_MIN or not dims_ok
    if geometry_changed:
        failures.append(f"subject geometry changed (silhouette IoU {iou:.4f})")

    interior = src[:, :, 3] >= OPAQUE_MIN
    face = np.zeros_like(interior)
    if interior.any():
        ys, xs = np.where(interior)
        y0, y1 = int(ys.min() + 0.18 * (ys.max() - ys.min())), int(ys.min() + 0.62 * (ys.max() - ys.min()))
        x0, x1 = int(xs.min() + 0.28 * (xs.max() - xs.min())), int(xs.min() + 0.72 * (xs.max() - xs.min()))
        face[y0:y1, x0:x1] = True
        face &= interior

    down = box_downscale(out[:, :, :3], SCALE)
    down_l = box_downscale(lanczos[:, :, :3], SCALE)
    src_rgb = src[:, :, :3].astype(np.float32)
    mae_identity = float(np.mean(np.abs(down.astype(np.float32)[interior] - src_rgb[interior]))) if interior.any() else 0.0
    mae_lanczos = float(np.mean(np.abs(down_l.astype(np.float32)[interior] - src_rgb[interior]))) if interior.any() else 0.0
    mae_face = float(np.mean(np.abs(down.astype(np.float32)[face] - src_rgb[face]))) if face.any() else 0.0

    face_structurally_altered = mae_face > IDENTITY_MAE_MAX
    if face_structurally_altered:
        failures.append(f"opaque facial pixels structurally altered (face MAE {mae_face:.3f})")
    if mae_identity > IDENTITY_MAE_MAX:
        failures.append(f"identity drift too high (MAE {mae_identity:.3f})")

    mask2 = lanczos[:, :, 3] >= OPAQUE_MIN
    detail_out = laplacian_var(out[:, :, :3], mask2)
    detail_l = laplacian_var(lanczos[:, :, :3], mask2)
    detail_ratio = detail_out / detail_l if detail_l > 0 else 0.0
    better_than_resize = detail_ratio >= DETAIL_RATIO_MIN
    if not better_than_resize:
        failures.append(
            f"not more detailed than Lanczos resize (laplacian ratio {detail_ratio:.3f})"
        )

    changed = int(np.any(out[:, :, :3] != lanczos[:, :, :3], axis=2).sum()) if out.shape == lanczos.shape else out.shape[0] * out.shape[1]
    generated = False
    if mae_identity > mae_lanczos + 4.0:
        generated = True
        failures.append("upscale drifted from source more than Lanczos; possible invented content")

    if oom:
        failures.append("out of memory")

    return {
        "source_dimensions": [src_w, src_h],
        "output_dimensions": [out_w, out_h],
        "scale_factor": SCALE,
        "processing_time_seconds": round(elapsed_s, 3),
        "alpha_preserved": "YES" if alpha_preserved else "NO",
        "silhouette_iou_vs_lanczos_alpha": round(iou, 6),
        "number_of_pixels_changed_vs_lanczos": changed,
        "geometry_changed": "YES" if geometry_changed else "NO",
        "opaque_facial_pixels_structurally_altered": "YES" if face_structurally_altered else "NO",
        "face_identity_mae": round(mae_face, 4),
        "interior_identity_mae": round(mae_identity, 4),
        "lanczos_identity_mae": round(mae_lanczos, 4),
        "detail_laplacian_var_upscale": round(detail_out, 4),
        "detail_laplacian_var_lanczos": round(detail_l, 4),
        "detail_ratio_vs_lanczos": round(detail_ratio, 4),
        "generated_invented_content": "YES" if generated else "NO",
        "ram_or_memory_issues": "YES" if oom else "NO",
        "failures": failures,
        "quality_gate": "FAIL" if failures else "PASS",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="2x non-generative RGBA upscale.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("projects/P001/prepared/person-refined-v01.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("projects/P001/prepared/person-upscaled-v01.png"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/P001/person-upscale-v01.json"),
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("image-preparation/models/RealESRGAN_x2plus.onnx"),
    )
    parser.add_argument("--tile", type=int, default=TILE)
    parser.add_argument(
        "--expect-size",
        default=None,
        help="Optional WxH check (example: 904x746). Omitted for general use.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    oom = False
    report: dict = {
        "pipeline": "MEMORIAL_PORTRAIT_PREP_UPSCALE_2X",
        "input": str(args.input),
        "output": str(args.output),
        "model_method": "Real-ESRGAN x2plus ONNX (CPU, non-generative; full-frame with pad-to-multiple-of-4, tiled fallback)",
        "model_path": str(args.model),
        "alpha_method": "Lanczos 2x on existing alpha (silhouette preserved)",
    }
    try:
        if not args.input.exists():
            raise FileNotFoundError(f"Input not found: {args.input}")
        src = load_rgba(args.input)
        model_path = ensure_model(args.model)
        session = make_session(model_path)
        inp = session.get_inputs()[0]
        report["onnx_input"] = {"name": inp.name, "shape": [str(s) for s in inp.shape], "type": inp.type}
        report["model_bytes"] = model_path.stat().st_size

        t0 = time.perf_counter()
        out = upscale_rgba(src, session, tile=args.tile)
        elapsed = time.perf_counter() - t0
        report["inference_mode"] = (
            "full-frame" if src.shape[0] <= args.tile and src.shape[1] <= args.tile else "tiled"
        )
        report["tile_size"] = args.tile

        out_size = (src.shape[1] * SCALE, src.shape[0] * SCALE)
        lanczos = np.dstack(
            [
                lanczos_resize(src[:, :, :3], out_size, "RGB"),
                lanczos_resize(src[:, :, 3], out_size, "L"),
            ]
        )
        gate = validate(src, out, lanczos, elapsed, oom=False)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(out, "RGBA").save(args.output, "PNG")
        report.update(gate)
        expect = args.expect_size or EXPECTED_SIZE
        if expect:
            if isinstance(expect, str):
                w_s, h_s = expect.lower().split("x")
                expect_size = (int(w_s), int(h_s))
            else:
                expect_size = tuple(expect)
            report["expected_dimensions"] = [expect_size[0], expect_size[1]]
            if (out.shape[1], out.shape[0]) != expect_size:
                report["quality_gate"] = "FAIL"
                report.setdefault("failures", []).append(
                    f"output is {out.shape[1]}x{out.shape[0]}, expected {expect_size[0]}x{expect_size[1]}"
                )
    except MemoryError:
        oom = True
        report.update(
            {
                "quality_gate": "FAIL",
                "failures": ["out of memory"],
                "ram_or_memory_issues": "YES",
                "generated_invented_content": "NO",
            }
        )
    except Exception as exc:
        msg = str(exc)
        oom = "out of memory" in msg.lower() or "oom" in msg.lower()
        report.update(
            {
                "quality_gate": "FAIL",
                "failures": [f"{type(exc).__name__}: {msg}"],
                "ram_or_memory_issues": "YES" if oom else "NO",
                "traceback": traceback.format_exc(),
            }
        )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report.get("quality_gate") == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
