# Memorial Master Template — V1

Source of truth for reusable memorial posters.

The Figma prototype **PROJECT 03 — MCP TEST / MCP TEST FRAME** is a successful experiment. It must not be destroyed, duplicated-as-master, or redesigned.

## Architecture

```
MASTER (immutable)
  → create a fresh instance
  → populate PERSON_SCHEMA.json fields
  → insert Image Preparation Engine portrait (1080×810 RGBA)
  → export
```

Image preparation is a separate pipeline (`image-preparation/`). Figma only places the finished asset.

## Figma

| Item | Value |
|---|---|
| File | PROJECT 03 — MCP TEST |
| Master frame | `MASTER MEMORIAL TEMPLATE — V1` |
| Canvas | 1080 × 1920 |
| Portrait zone | 1080 × 810 |
| Test instance | `MEMORIAL — TEST PERSON 001` |

## Zones

| Zone | Layer | Schema field(s) |
|---|---|---|
| A | Header / Archive | `id` / archive mark |
| B | Portrait Zone | prepared PNG (not in schema) |
| C | Name FA | `persian_name` |
| D | Name EN | `english_name` |
| E | Dates | `birth_date`, `death_date` |
| F | Location | `location` |
| G | Identifier / Title | `identifier` |
| H | Memorial Statement | `memorial_statement_fa`, `memorial_statement_en` |
| I | Biography | `biography_fa`, `biography_en` |
| J | Optional Information | `optional_information` |
| K | Footer / Archive Mark | archive mark |

Master copy is placeholder-only. No person-specific facts live on the master.

## Lock

CONTENT MAY CHANGE. DESIGN MUST NOT CHANGE.

See `DESIGN_RULES.md`.

## Related files

- `PERSON_SCHEMA.json` — content contract
- `DESIGN_RULES.md` — geometry, type, color, permissions
- `assets/` — template-local notes only; production portraits stay under `/assets/prepared/`
