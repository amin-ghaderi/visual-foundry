# Memorial Design Pipeline

Production pipeline for editorial memorial posters.

ChatGPT directs. Cursor executes. ComfyUI prepares cutouts. Figma is the visual source of truth.

## 1. What this project is

A four-layer system:

1. **Creative** — ChatGPT as Art Director
2. **Handoff** — a brief, in any reasonable format
3. **Execution** — Cursor as orchestrator (`pipeline/`)
4. **Production** — local image engine + Figma MCP + exports from Figma

This repository does **not** generate faces and does **not** invent biography.

## 2. Folder structure

```text
README.md
DESIGN_PROTOCOL.md
CURSOR_AGENT.md
DESIGN_HANDOFF_PROTOCOL.md
config.yaml
AUDIT_REPORT.md

pipeline/                  CLI orchestrator
image-preparation/         validated image engine + Real-ESRGAN model + BiRefNet workflow
templates/memorial/        memorial template spec (Figma master not built yet)
templates/parman-padeshahi-iranian/  PMPI-MASTER-V10 locked editorial Master
projects/P001/             first subject (Test Person)
archive/legacy/            obsolete experiments, kept on purpose
reports/                   pipeline and project reports
```

Each project:

```text
projects/P001/
  project.yaml
  LATEST.md
  input/                   original photograph only
  prepared/                cutout / refine / upscale / final plate
  handoff/                 briefs
  figma/                   file key, URL, frame id (no credentials)
  exports/                 PNG/JPG from approved Figma frames
  versions/
```

## 3. How to create a project

```text
python pipeline/run.py create-project
python pipeline/run.py create-project --template memorial
```

This assigns the next free ID (`P001`, `P002`, …), creates folders, and writes `project.yaml`. IDs are never reused.

Drop the original photograph into `projects/PXXX/input/`. Never overwrite it later.

## 4. How to provide a ChatGPT Design Handoff

Put the brief in `projects/PXXX/handoff/` (Markdown, JSON, or plain text). Attach images there or in `input/`.

ChatGPT does not need to know this repo. Cursor reads `DESIGN_HANDOFF_PROTOCOL.md` and translates the brief.

```text
python pipeline/run.py interpret-handoff --project P001
```

## 5. How image preparation works

Prefer `pipeline/run.py`. The engine scripts under `image-preparation/` are the validated stages:

| Stage | Tool | When |
|---|---|---|
| Background removal | ComfyUI BiRefNet | Photograph is opaque / has a real background |
| Edge refine | `edge_refine.py` | After a cutout |
| 2× upscale | Real-ESRGAN x2plus ONNX CPU | Only if the subject is smaller than the 1080×810 plate |
| Final plate | 1:1 compose | Memorial portrait zone |

Identity-preserving rules: no face restore, no generative inpainting, no overwrite of `input/`.

```text
python pipeline/run.py prepare-image --project P001
python pipeline/run.py prepare-image --project P001 --execute
```

Without `--execute`, the command plans stages and checks existing files.

## 6. How Figma MCP is used

After the portrait plate exists, Cursor uses Figma MCP to build native frames, type, auto layout, variables, and image fills.

- Figma is the design source of truth.
- Do not flatten the poster into one image.
- If a Master exists, instance it. Never copy person N to make person N+1.
- Record the file in `projects/PXXX/figma/figma.yaml`.

The memorial Master is specified in `templates/memorial/` but is **not yet built in Figma**. The existing prototype **PROJECT 03 — MCP TEST / MCP TEST FRAME** must not be destroyed.

## 7. How versions work

`v01`, `v02`, `v03`. One current version in `project.yaml`.

Examples: `person-refined-v01.png`, `handoff-v01.md`, `memorial-P001-v01.png`.

`person-final.png` is the current approved plate for that project (a pointer name, not a duplicate dump of every revision).

## 8. How to find the latest output

1. `projects/PXXX/LATEST.md`
2. `projects/PXXX/project.yaml` fields `latest_asset`, `latest_handoff`, `latest_figma`, `latest_export`
3. `python pipeline/run.py status --project PXXX`

Do not duplicate large PNGs only to mark them “latest”.

## 9. How to validate a project

```text
python pipeline/run.py validate
python pipeline/run.py validate --project P001
python pipeline/run.py status --project P001
```

## Commands

```text
python pipeline/run.py create-project
python pipeline/run.py prepare-image --project P001
python pipeline/run.py validate --project P001
python pipeline/run.py status --project P001
python pipeline/run.py export --project P001
```

Protected: ComfyUI install, Python environments, `.cursor/mcp.json`, Figma authentication, the ONNX model, original photographs.
