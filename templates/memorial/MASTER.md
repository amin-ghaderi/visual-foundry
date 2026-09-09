# Memorial Master Template — V1

Figma source of truth for **جاودانۀ ایران / Iran Memorial**.

**CONTENT MAY CHANGE. DESIGN MUST NOT CHANGE.**

Do not destroy or edit **PROJECT 03 — MCP TEST**. Do not derive a person from P001.

## Figma

| Item | Value |
|---|---|
| File | MASTER MEMORIAL — JAVIDNAMEH IRAN — V1 |
| File key | `r0wjMmdUI50iaGsxCzBnCG` |
| URL | https://www.figma.com/design/r0wjMmdUI50iaGsxCzBnCG |
| Master component | `MASTER MEMORIAL TEMPLATE — V1` (`7:2`) |
| Canvas | **1080 × 1350** (Instagram portrait) |
| Portrait slot | `PORTRAIT_SLOT` (`7:13` on the master instance) |

## Portrait placement

Insert the prepared transparent PNG into layer **PORTRAIT_SLOT**.

- Expected asset: `projects/PXXX/prepared/person-final.png`
- Expected size: **1080 × 810 RGBA** (image pipeline plate)
- Figma scale: **FIT** — do not stretch
- The slot is **524 × 780** on the poster (left column). The plate is letterboxed inside it.
- Do not generate a portrait. Do not use AI imagery.

## Production path

```
MASTER MEMORIAL TEMPLATE — V1
  → create a fresh instance
  → fill PERSON_SCHEMA / component properties
  → insert prepared PNG into PORTRAIT_SLOT
  → export
```

Never: Person N → duplicate → Person N+1.

## Layout

Two-column editorial:

- Left ~55% content width: `PORTRAIT_SLOT`
- Right ~45%: identity, facts, cause of death, biography
- Outer margin 64 px
- Subtle vertical divider

## Components

MEMORIAL_HEADER · PORTRAIT_SLOT · CONTEXT_LABEL · NAME_BLOCK · DATE_BLOCK · FACT_BLOCK · CAUSE_OF_DEATH · BIOGRAPHY_BLOCK · MEMORIAL_STATEMENT · MEMORIAL_FOOTER

Master copy is placeholder-only.
