# Memorial Master — Design Rules

**CONTENT MAY CHANGE. DESIGN MUST NOT CHANGE.**

This file is the contract between the Master Template and Cursor.

## Canvas

| Token | Value |
|---|---|
| Canvas name | `MASTER MEMORIAL TEMPLATE — V1` |
| Width | 1080 px |
| Height | 1920 px |
| Orientation | Portrait |
| Units | Pixels |

The extra height beyond the 1080×1350 prototype is reserved for biography, optional information, and footer. Do not shrink the canvas to fit one person.

## Portrait zone

| Token | Value |
|---|---|
| Layer | `Portrait Zone` |
| Size | **1080 × 810 px** |
| Asset | Prepared RGBA PNG from the Image Preparation Engine |
| Scale | 1:1 — `FIT`, never stretch |
| Crop | None, unless the existing mask/clip already defined in the master |
| Position | Full-bleed, directly under Header / Archive |

Figma must **not** prepare, upscale, restore, or regenerate portraits.

## Grid and margins

| Token | Value |
|---|---|
| Layout grid | 1 column, 64 px left/right margin on editorial blocks |
| Portrait | 0 margin (full bleed) |
| Editorial inset | 64 px |
| Vertical rhythm | 8 px base; use 16 / 24 / 32 / 48 / 64 |

## Spacing scale

| Token | px |
|---|---|
| `spacing/2xs` | 8 |
| `spacing/xs` | 16 |
| `spacing/sm` | 24 |
| `spacing/md` | 32 |
| `spacing/lg` | 48 |
| `spacing/xl` | 64 |

## Color system

Monochrome / ink on paper. No decorative color.

| Semantic | Use |
|---|---|
| `color/bg/paper` | Editorial field, master canvas |
| `color/bg/portrait` | Portrait well (black field behind PNG alpha) |
| `color/text/primary` | Names, statement, biography |
| `color/text/secondary` | Dates, location, identifier |
| `color/text/muted` | Footer, archive meta |
| `color/text/inverse` | Header label on portrait field |
| `color/rule` | Hairline separators only |

No gradients. No drop shadows. No colored overlays.

## Typography hierarchy

### English

| Style | Family | Size | Use |
|---|---|---|---|
| `Label/Archive` | Inter Medium | 11 | Header / footer marks |
| `Name/EN` | Playfair Display Regular | 28 | English name |
| `Meta` | Inter Regular | 13 | Dates, location, identifier |
| `Statement/EN` | Inter Regular | 16 | Memorial statement |
| `Body/EN` | Inter Regular | 14 | Biography, optional |
| `Footer` | Inter Medium | 10 | Archive footer |

### Persian

| Style | Family | Size | Use |
|---|---|---|---|
| `Name/FA` | Vazirmatn Medium | 56 | Persian name |
| `Statement/FA` | Vazirmatn Medium | 18 | Persian statement |
| `Body/FA` | Vazirmatn Regular | 16 | Persian biography |

### Persian rules

- Right-to-left.
- Vazirmatn only for Persian runs. Do not substitute Arabic-lookalike display fonts.
- Do not mix Persian and English in one text node.
- Keep the Persian name above the English name.

### English rules

- Playfair Display for the English name only.
- Inter for meta, body, labels.
- No all-caps on the memorial statement or biography.
- Archive labels may be small caps / tracking.

## Component structure

```
MASTER MEMORIAL TEMPLATE — V1
├── Header / Archive
├── Portrait Zone
├── Identity Block
│   ├── Name FA
│   ├── Name EN
│   ├── Dates
│   ├── Location
│   └── Identifier
├── Memorial Statement
├── Biography
├── Optional Information
└── Footer
```

## Layer naming

Use the names above. Do not rename master layers to a person's name.

## What is locked (NEVER change)

- Canvas size
- Portrait zone size (1080×810)
- Grid, margins, spacing scale
- Type families, sizes, line-height, letter-spacing
- Color tokens
- Auto Layout structure and stacking order
- Component geometry
- Master frame name
- Prototype frame `MCP TEST FRAME`

## What is variable (MAY change on instances only)

Fields in `PERSON_SCHEMA.json`:

- `persian_name`, `english_name`
- `birth_date`, `death_date` (rendered as `YYYY — YYYY`)
- `location`, `identifier`
- `memorial_statement_fa`, `memorial_statement_en`
- `biography_fa`, `biography_en`
- `optional_information`
- Prepared portrait image fill inside `Portrait Zone`

Empty schema fields stay as master placeholders (`—` or hidden via boolean properties). Do not invent facts.

## What Cursor is allowed to change

On a **fresh instance** of the master:

- Text content listed above
- Portrait image fill (validated 1080×810 PNG only)
- Visibility of empty optional blocks

## What Cursor must NEVER change

- The master component itself after lock
- `MCP TEST FRAME` / Project 03 prototype
- Original photographs
- Image-preparation pipeline code, unless a separate pipeline task says so
- Layout, type, color, effects, slogans, icons, gradients
- Portrait geometry (no stretch, no extra crop, no face restore)

## Production path

```
MASTER → create fresh instance → populate schema → insert prepared portrait → export
```

Never: Person 001 → modify → Person 002.
Never redesign the master because of one photograph.
