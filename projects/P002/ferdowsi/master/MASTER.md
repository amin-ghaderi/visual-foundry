# FERDOWSI-VERSE-MASTER

SERIES MASTER STATUS: FINAL / LOCKED / APPROVED  
ID: `FERDOWSI-VERSE-MASTER`  
Figma frame: `80:2`  
Position: `100, 11000`  
Canvas: `1080 × 1080`

File: ECONOMIC D-DAY — IRAN — P002  
Key: `1Hlx23O0YeWSPJ5NgMBZWg`  
URL: https://www.figma.com/design/1Hlx23O0YeWSPJ5NgMBZWg

This literary series has **one** visual master. It is **not** PMPI-MASTER-V10. Do not edit V10. Do not redesign this series. Do not create a competing Ferdowsi layout. Do not add photographs, portraits, illustrations, flags, or generated artwork. The Shahnameh verse is the visual hero.

## Official chrome (LOCKED)

### Section title

`شاهنامه برای امروز`

Spelling is locked. Do not use `شاهنامه‌خوانی` or `یک بیت برای ایران`.

### Top-right

```text
پارمان پادشاهی ایرانیان
Iranian Monarchy Party
```

Do not use `حزب پادشاهی ایرانیان` on Ferdowsi slides. (V10 economic slides keep `حزب`.)

Left masthead `IRANIAN MONARCHY PARTY` and the logo stay unchanged.

### Bottom-right

`پارمان پادشاهی ایرانیان`

### Bottom-left — verse identifier only

Persian digits. No slash. No em dash. No Instagram/page-count notation.

Examples: `۰۰۱` `۰۰۲` `۰۰۳` `۰۱۰` `۰۲۵` `۰۸۵` `۲۰۰`

Do **not** display `03 / 14`, `01 / 14`, or `01  —  14` on Ferdowsi content slides.

Cover-range numbering (em dash) belongs to campaign covers only, not this series.

Typography: Vazirmatn Medium, 18px, gold `#C8A94B`, left of the footer band. Slightly larger than V10 page numbers; do not enlarge further.

## Mechanism

```text
FERDOWSI-VERSE-MASTER
→ DUPLICATE
→ REPLACE TEXT ONLY
→ CHANGE VERSE NUMBER ONLY
→ EXPORT
```

Clone frame `80:2` only. Mutate the clone by node ID. Never redesign. Never clone `2:2`. Never touch Economic D-Day frames (`59:*`, cover `67:2`).

Populate the master. Do not design a new Ferdowsi slide.

## What may change on a duplicate

1. Verse
2. Glossary
3. به زبان امروز
4. Source / story
5. Verse number (`FOOT_NUM`)

Hide `NOTE_FA` when the handoff supplies no interpretation. Do not invent one.

## What must not change

Background, logo, logo position, header layout, typography family and hierarchy, ivory text, restrained gold, lion watermark, gold rules, margins, spacing system, glossary structure, modern-language section placement, source placement, footer structure, section label, top-right organization name, bottom-right organization name.

## Orthography

Do not normalize Persian. Preserve supplied diacritics exactly. Do not add or remove marks.

Verse quotation marks in a handoff are **not** rendered. The verse itself does not display `« »`.

Glossary heading uses ZWNJ: `واژه‌گان`.

## Master layers (`80:2`)

| Layer | ID | Locked / variable |
|---|---|---|
| LION_MOTIF | `80:3` | LOCKED — `BG-WHITE.png`, 640×640 at 220,220, fill opacity 0.16 |
| LOGO | `80:4` | LOCKED — 106×92 at 72,50 |
| MAST_FA | `80:5` | LOCKED — پارمان پادشاهی ایرانیان / Iranian Monarchy Party |
| MAST_EN | `80:6` | LOCKED — IRANIAN MONARCHY PARTY |
| HEADER_RULE | `80:7` | LOCKED — gold, y=164 |
| FOOT_NUM | `80:8` | VARIABLE — Persian verse id; master shows `۰۰۱` |
| FOOT_SERIES | `80:9` | LOCKED — پارمان پادشاهی ایرانیان |
| FOOTER_RULE | `80:10` | LOCKED — gold, y=996 |
| TITLE_FA | `81:2` | LOCKED — شاهنامه برای امروز |
| VERSE_FA | `84:2` | VARIABLE — verse |
| BODY_RULE | `80:13` | LOCKED — gold rule under verse |
| GLOSS_HEAD | `81:4` | LOCKED — واژه‌گان |
| GLOSS_FA | `81:5` | VARIABLE — glossary |
| TODAY_HEAD | `81:6` | LOCKED — به زبان امروز |
| TODAY_FA | `81:7` | VARIABLE — modern language |
| NOTE_FA | `81:8` | VARIABLE — hide when unused |
| SOURCE_FA | `81:9` | VARIABLE — source / story |

Hidden leftover economic layers (keep hidden on clones): KICKER `80:11`, HEAD_FA `80:12`, BODY_FA `80:14`, KEY_RULE `80:15`, KEY_FA `80:16`.

## Visual reference PNG

Current locked chrome: `projects/P002/ferdowsi/master/ferdowsi-verse-master-001-v03-2x.png`

Previous chrome snapshots (do not delete):

- `projects/P002/ferdowsi/master/ferdowsi-verse-master-001-v02-2x.png`
- `projects/P002/ferdowsi/master/ferdowsi-verse-master-01-01-v01-2x.png`

Original campaign copy (do not delete):

- `projects/P002/exports/pmpi-01-01-yek-beyt-v01-2x.png`
- `projects/P002/versions/pmpi-01-01-yek-beyt-v01-2x.png`

## Published slides

| Slide | Frame | Verse id | Export |
|---|---|---|---|
| Master content (verse ۰۰۱) | `80:2` | `۰۰۱` | `ferdowsi/master/ferdowsi-verse-master-001-v03-2x.png` |
| Verse ۰۰۲ (final) | `91:2` | `۰۰۲` | `ferdowsi/exports/ferdowsi-P002-verse-002-v03-2x.png` |
