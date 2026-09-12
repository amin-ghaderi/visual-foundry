# PMPI-MASTER-V10 — Design Spec

**CONTENT MAY CHANGE. DESIGN MUST NOT CHANGE.**

This is the locked visual contract for `PMPI-MASTER-V10`.

Figma: https://www.figma.com/design/1Hlx23O0YeWSPJ5NgMBZWg  
Canonical frames: `2:2`, `2:17`, `2:34`, `2:57`, `13:2`

## Canvas

| Token | Value |
|---|---|
| Format | Instagram square |
| Width | 1080 px |
| Height | 1080 px |
| Export | PNG, scale 2 → 2160 × 2160 |
| Outer margin | 72 px |
| Header band | y = 0 to gold rule at y = 164 |
| Content band | y = 165 to 995 |
| Footer band | y = 996 to 1080 |

## Color

| Role | Hex | RGB 0–1 | Use |
|---|---|---|---|
| Canvas navy | `#0D1722` | 0.051, 0.090, 0.133 | Frame fill |
| Ivory | `#F4F1E8` | 0.957, 0.945, 0.910 | Primary type |
| Muted | `#A8A396` | 0.659, 0.639, 0.588 | Secondary type, English mast, footer org |
| Gold | `#C8A94B` | 0.784, 0.663, 0.294 | Rules (~38% opacity), page numbers |

No new palettes. No gradients. No glow. No neon.

## Type

| Role | Family | Style | Size | Tracking | Align |
|---|---|---|---|---|---|
| Top-right Persian | Vazirmatn | Medium | 16 | 0 | Right |
| Top-right English | Source Serif 4 | Regular | 11 | 0 | Right (second line of MAST_FA) |
| Top-left wordmark | Source Serif 4 | Regular | 13 | 90% | Left |
| Footer number | Source Serif 4 | Regular | 13 | 80% | Left |
| Footer org | Vazirmatn | Medium | 13 | 0 | Right |
| Body / headlines | Vazirmatn + Source Serif 4 | as on Master | — | — | RTL for Persian |

Do not introduce a third family. Do not restyle the header typefaces.

## Header (locked alignment)

Two groups on one horizontal header line.

**Top-left lockup**

| Layer | Geometry |
|---|---|
| `LOGO` | 106 × 92 at **72, 50**, image scale **FIT** |
| Asset | `projects/P002/prepared/brand-logo-transparent.png` (approved transparent logo) |
| `MAST_EN` | `IRANIAN MONARCHY PARTY` at **194, 72**, width 814, size 13 |

Logo artwork and proportions are frozen. Scale only as a uniform lockup; do not redraw, crop, or replace.

**Top-right organization block (`MAST_FA`)**

- Position: 184, 70, 824 × 36
- Line 1: `حزب پادشاهی ایرانیان`
- Line 2: `Iranian Monarchy Party`

**Gold header rule**

- `HEADER_RULE` at 72, 164, 936 × 1, gold `#C8A94B` at 38% opacity

## Lion watermark

| Token | Value |
|---|---|
| Layer | `LION_MOTIF` |
| Asset | `projects/P002/prepared/BG-WHITE.png` |
| Size / position | 640 × 640 at 220, 220 (center 540, 540) |
| Scale | FIT |
| Fill opacity | 0.16 |
| Blend | NORMAL |

Lion only (face, mane, crown). No ring, no full emblem, no logo text in the watermark.

## Footer

| Layer | Geometry / copy |
|---|---|
| `FOOTER_RULE` | 72, 996, 936 × 1, gold 38% |
| `FOOT_NUM` | 72, 1016, gold, `01  /  05` style (update numbers per slide) |
| `FOOT_SERIES` | 620, 1016, muted, `پارمان پادشاهی ایرانیان` |

No extra slogan. No English line in the footer.

## Layout rules

- Keep 72 px side margins.
- Keep both gold rules.
- Content lives strictly between the rules.
- Additional slides are duplicates of a Master frame, not new layouts.
- Readability beats squeezing copy.
