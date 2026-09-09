# Project Audit Report

Audited: 2026-09-08  
Root: `C:\Users\Public\Myapps\Design\project01`  
Method: recursive listing + SHA-256 for every relevant file  
Action taken after this report: architecture refactor **executed**. Active files now live under `projects/P001/`, `templates/memorial/`, `pipeline/`, and `archive/legacy/2026-09/`. No UNKNOWN files were deleted.

Classification keys:

- **KEEP** — required by the active pipeline; stay in place or stay active after a path update
- **MOVE** — still active, but relocated into the target structure
- **ARCHIVE** — obsolete or duplicate; copied to `archive/legacy/` before any source removal
- **REPLACE** — superseded by a new file in the target structure
- **DELETE-SAFE** — regenerable cache only
- **UNKNOWN** — not deleted

---

## 1. Old structure (before refactor)

```
project01/
  test-person-original.png          (root duplicate)
  .cursor/mcp.json
  assets/
    test-person-original.png
    test-person-prepared.png
    prepared/                       mixed workflow + all pipeline PNGs
    raw/.gitkeep
  image-preparation/
    edge_refine.py
    smart_portrait_crop.py
    upscale_2x.py
    final_portrait_asset.py
    models/RealESRGAN_x2plus.onnx
    reports/*.json
    __pycache__/
  templates/memorial-master/
  outputs/memorial/.gitkeep
```

There was no project ID system, no CLI orchestrator, no version protocol, and raw/prepared/export files were mixed.

---

## 2. Inventory and classification

### Configuration / MCP

| Item | Bytes | SHA-256 | Class | Notes |
|---|---:|---|---|---|
| `.cursor/mcp.json` | 577 | `1EB92D3ECEE38FA0…70668FA0` | **KEEP** | Comfy MCP only. Do not modify. Figma MCP is user-level, not in this file. |

### Source photographs

| Item | Bytes | SHA-256 | Class | Notes |
|---|---:|---|---|---|
| `assets/test-person-original.png` | 247475 | `16C01E49020258D534C0C24A960CF83DA3EED607B171B062061E1819B0B25EFE` | **MOVE** | Authoritative original. → `projects/P001/input/person-original.png`. Never overwrite. |
| `test-person-original.png` (root) | 247475 | identical to above | **ARCHIVE** | Byte-identical duplicate. |

### Prepared / experiment images

| Item | Bytes | SHA-256 | Class | Notes |
|---|---:|---|---|---|
| `assets/prepared/test-person-birefnet.png` | 257839 | `2C0EE261E3B4FB2F1F3D48D7DC16B8ECD4DF6C8D925D5ED814D37E0B3186BE62` | **MOVE** | Validated BiRefNet cutout → `projects/P001/prepared/person-birefnet-v01.png` |
| `assets/prepared/test-person-birefnet-base.png` | 257839 | identical to birefnet.png | **ARCHIVE** | Intentional copy created by `edge_refine.py`. Duplicate. |
| `assets/prepared/test-person-birefnet-refined.png` | 102903 | `35FEC7686E94AE85CD18138603A1AA40837A4F0EE9E71E803B38B959CFC97FFB` | **MOVE** | Validated refine → `person-refined-v01.png` |
| `assets/prepared/test-person-birefnet-refined-2x.png` | 432211 | `145BC21CB47FAE23B359BE16A68B0795A82F139DC484B750154D5ED76A11050A` | **MOVE** | Validated 2× → `person-upscaled-v01.png` |
| `assets/prepared/test-person-final-portrait-1080x810.png` | 440529 | `64747C1E99D114DD8D66BFA9EDF1C5D54D039AD453886091B7F73C83E36AFA7E` | **MOVE** | Current master portrait → `person-final.png` |
| `assets/test-person-prepared.png` | 165264 | `CF81BC5EC3780C873DD2A0C02E1C8567B5A204E4BECD178AF36D107D1534F411` | **ARCHIVE** | Pre-pipeline experiment. Unique. Not in the V1.4 chain. |
| `assets/prepared/test-person-portrait-1080x810.png` | 239396 | `79A2A51C5A27245D2F9CF265E40DBE25BCDE88ADF4E9506418A29AE4DA93B703` | **ARCHIVE** | Superseded V1.2 crop (pre-upscale). |
| `assets/prepared/test-person-portrait-1080x810-v2.png` | 114376 | `62653D3968F8BD41A1120F884E71D8AF338E17B8E78A773593BB75447F7AA2EF` | **ARCHIVE** | Superseded corrected crop. Replaced by V1.4 final. |

### Image engine (Python)

| Item | Class | Notes |
|---|---|---|
| `image-preparation/edge_refine.py` | **KEEP** | Validated local defringe. Reused by `pipeline/prepare_image.py`. |
| `image-preparation/smart_portrait_crop.py` | **KEEP** | Geometry-only 1:1 crop. |
| `image-preparation/upscale_2x.py` | **KEEP** | Real-ESRGAN x2plus ONNX CPU. Hardcoded 904×746 expect-size will be made optional. |
| `image-preparation/final_portrait_asset.py` | **KEEP** | 1080×810 compose. Filename lock will be relaxed so the engine is reusable. |
| `image-preparation/models/RealESRGAN_x2plus.onnx` | **KEEP** | 67,191,666 bytes. Do not move off disk; do not delete. |
| `image-preparation/__pycache__/` | **DELETE-SAFE** | Regenerable bytecode. |

### Workflows

| Item | Class | Notes |
|---|---|---|
| `assets/prepared/birefnet-test-workflow.json` | **MOVE** | Active ComfyUI API-format graph → `image-preparation/workflows/birefnet.json` |

### Reports

| Item | Class | Notes |
|---|---|---|
| `image-preparation/reports/test-person-birefnet-refined.json` | **MOVE** | → `reports/P001/` |
| `image-preparation/reports/test-person-upscale-2x.json` | **MOVE** | → `reports/P001/` |
| `image-preparation/reports/test-person-final-portrait-v1-4.json` | **MOVE** | → `reports/P001/` |
| `image-preparation/reports/test-person-portrait-v1-2.json` | **ARCHIVE** | Superseded crop report |
| `image-preparation/reports/test-person-portrait-v1-2-corrected.json` | **ARCHIVE** | Superseded crop report |

### Templates

| Item | Class | Notes |
|---|---|---|
| `templates/memorial-master/MASTER_TEMPLATE.md` | **MOVE** + **REPLACE** | Archive original; active copy becomes `templates/memorial/MASTER.md` |
| `templates/memorial-master/DESIGN_RULES.md` | **MOVE** + **REPLACE** | Archive original; active copy becomes `templates/memorial/DESIGN_SPEC.md` |
| `templates/memorial-master/PERSON_SCHEMA.json` | **MOVE** | → `templates/memorial/PERSON_SCHEMA.json` |
| `templates/memorial-master/.ds-state.json` | **MOVE** | Incomplete Figma master state → `templates/memorial/figma-state.json` |
| `templates/memorial-master/assets/.gitkeep` | **MOVE** | Empty placeholder |

Master Template in Figma is **not built**. Do not design it during this refactor.

### Placeholders / empty dirs

| Item | Class | Notes |
|---|---|---|
| `assets/raw/.gitkeep` | **ARCHIVE** | Replaced by `projects/PXXX/input/` |
| `outputs/memorial/.gitkeep` | **ARCHIVE** | Replaced by `projects/PXXX/exports/` |

### External (not in this repo — protected)

| Item | Class | Notes |
|---|---|---|
| ComfyUI install `C:\Users\info\comfy` | **KEEP** | Do not reinstall |
| `C:\Users\info\comfy-env` | **KEEP** | Do not modify |
| Figma MCP auth (user-level) | **KEEP** | Do not change |
| Figma file `y7s7wj1KvlA01cyqlaJZDy` (PROJECT 03 — MCP TEST) | **KEEP** | Prototype. Do not destroy or redesign. |
| Figma file `FKHBoJKesfSEFP0X9X8X0D` (MCP WRITE ACCESS TEST) | **KEEP** | Temporary write-access probe. Do not modify. |

### Missing before refactor (to create)

README.md, DESIGN_PROTOCOL.md, CURSOR_AGENT.md, DESIGN_HANDOFF_PROTOCOL.md, config.yaml, `pipeline/*`, `projects/P001/*`, `archive/legacy/`.

---

## 3. Duplicate detection

High confidence (identical SHA-256 + size):

1. Root `test-person-original.png` == `assets/test-person-original.png`
2. `test-person-birefnet.png` == `test-person-birefnet-base.png`

Not duplicates (different hashes): all other PNGs, including `*-prepared.png` and both 1080×810 crop experiments vs the V1.4 final.

No automatic deletion of duplicates. Duplicates are archived.

---

## 4. Proposed archive set (`archive/legacy/2026-09/`)

- `test-person-original.png` (root duplicate)
- `assets/test-person-prepared.png`
- `assets/prepared/test-person-birefnet-base.png`
- `assets/prepared/test-person-portrait-1080x810.png`
- `assets/prepared/test-person-portrait-1080x810-v2.png`
- `image-preparation/reports/test-person-portrait-v1-2.json`
- `image-preparation/reports/test-person-portrait-v1-2-corrected.json`
- `templates/memorial-master/` (originals, after active copies exist)
- empty `.gitkeep` placeholders under `assets/raw` and `outputs/memorial`

## 5. Proposed move set (active)

- Original + validated chain → `projects/P001/`
- BiRefNet workflow → `image-preparation/workflows/`
- V1.4 reports → `reports/P001/`
- Template docs → `templates/memorial/`

## 6. Do not delete

- UNKNOWN: none identified
- Model ONNX file
- Working Python engine scripts
- `.cursor/mcp.json`
- Original photograph bytes (only relocate)

---

## 7. Safety notes

- Image preparation remains a separate engine from Figma.
- P001 is the existing Test Person subject. No new memorial design is created in this refactor.
- Figma Master Template construction is out of scope for this refactor.
