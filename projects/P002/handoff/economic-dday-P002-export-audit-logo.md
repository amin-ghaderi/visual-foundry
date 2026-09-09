# P002 — export quality audit (logo sharpness)

Date: 2026-09-09
Figma file: ECONOMIC D-DAY — IRAN — P002 (`1Hlx23O0YeWSPJ5NgMBZWg`)
Current master: v08
Logo replaced: no
Design changed: no
New Figma file: no

## 1. Logo asset in Figma

All five `LOGO` layers (`2:4`, `2:19`, `2:36`, `2:59`, `13:4`) are RECTANGLE nodes with an IMAGE fill (raster PNG), not vector/SVG.

- Source file: `projects/P002/prepared/brand-logo-transparent.png`
- Format: PNG, RGBA, transparent background
- Native pixels: **1280 × 1111**
- Bytes: 881413
- Figma imageHash: `0e41c6c0e2d1aada29559faff511c471f96944f7`
- Byte-identical to the prepared file
- Slot: x=72, y=64, w=92, h=80, scaleMode FIT
- No SVG/vector of this logo exists in `projects/P002/`
- `input/brand-logo.jpg` was not used

The placed asset is **not** low-resolution relative to the 92×80 slot (~14× oversampled). It was not replaced.

## 2. Export mechanism

Native Figma frame export via `download_assets` on each 1080×1080 frame (Figma PNG export at scale 1). Not `get_screenshot`, not a canvas capture.

`svgAssets` on every frame: empty.

## 3. Where sharpness is lost

Inside Figma, zoom samples the **1280 × 1111** fill.

A 1× 1080×1080 PNG rasterizes the logo to **92 × 80 pixels**. Zooming that PNG upscales ~80 px. That is the blur. It is not a screenshot pipeline and not a small raster placed in Figma.

Native 1× exports of this file are **byte-identical** to current v08:

| Frame | Native 1× bytes | Matches |
|---|---|---|
| 01 `2:2` | 269600 | `economic-dday-P002-01-v08.png` |
| 02 `2:17` | 261709 | `…-02-v08.png` |
| 03 `2:34` | 270847 | `…-03-v08.png` |
| 04 `2:57` | 275874 | `…-04-v08.png` |
| 05 `13:2` | 284594 | `…-05-v08.png` |

Logo node 1× export: 92×80 PNG. Frames 01 and 02 produced the identical 92×80 file.

## 4. What was not done

- Logo not enlarged or moved
- Artwork not redrawn or regenerated
- v07 filenames not overwritten (v07 is the prior BG-WHITE revision; current master is v08)
- No new version written (native re-export equals v08)

A 1080×1080 file cannot keep Figma-zoom logo sharpness while the logo stays 92×80. A 2×/3× frame export (2160/3240) would, but that is not 1080×1080.
