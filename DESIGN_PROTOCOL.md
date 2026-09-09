# Design Protocol

This project is a production design pipeline. Cursor executes it. Figma is the visual source of truth.

## Four layers

### Layer 1 — Creative

ChatGPT is the Art Director. It decides what the design should communicate.

ChatGPT does not need to know Cursor, Python, ComfyUI, Figma MCP, file paths, or this repository.

### Layer 2 — Handoff

ChatGPT produces a Design Handoff. The handoff may be:

- natural language
- structured Markdown or JSON
- a brief plus images
- a template name plus content
- a mix of the above

The contract is `DESIGN_HANDOFF_PROTOCOL.md`.

### Layer 3 — Execution

Cursor is the Design Execution Agent and Pipeline Orchestrator.

Cursor always follows `CURSOR_AGENT.md`:

1. Read this protocol.
2. Identify the project (`P001`, `P002`, …).
3. Interpret the handoff.
4. Run only the pipeline stages that are required.
5. Implement the visual design in Figma.
6. Validate and export.
7. Update `project.yaml`.

### Layer 4 — Production

- **ComfyUI** prepares image assets that need background removal (BiRefNet).
- **Local Python** (`image-preparation/`) refines edges, crops, upscales when needed, and composes the portrait plate.
- **Figma MCP** builds the actual design from native Figma objects.
- **Exports** are PNG/JPG generated from the approved Figma frame, stored in `projects/PXXX/exports/`.

Do not flatten a poster into a single generated image.

## Source of truth

| Thing | Authority |
|---|---|
| Photograph identity | `projects/PXXX/input/` original file |
| Prepared portrait plate | `projects/PXXX/prepared/person-final.png` (or `latest_asset` in `project.yaml`) |
| Visual design | Figma file recorded in `projects/PXXX/figma/` |
| Content fields | Handoff + `templates/<name>/PERSON_SCHEMA.json` — never invented |
| Current version | `project.yaml` |

## Project IDs

Sequential, never reused: `P001`, `P002`, `P003`, …

```text
python pipeline/run.py create-project
```

creates the next ID automatically.

## Versions

Use `v01`, `v02`, `v03`. Never `final-final.png`, `new-final.png`, or `test-new.png`.

`portrait-final.png` / `person-final.png` means the current approved plate for that project, not a random extra copy.

## Image rules

- Never overwrite the original photograph.
- Never mix raw and prepared files.
- Prefer non-generative processing when identity must be preserved.
- Do not generate a new face.
- Do not automatically upscale every image.
- BiRefNet (ComfyUI) → edge refine → optional 2× Real-ESRGAN → 1:1 compose to 1080×810.

## Figma rules

- Native frames, text, vectors, components, variables, auto layout, image fills.
- If a Master Template exists, instance it. Never derive P002 from P001.
- Do not redesign a template unless the user explicitly asks for a new design.
- Do not destroy `MCP TEST FRAME` in PROJECT 03 — MCP TEST.

## What this refactor does not do

The Memorial Master Template is specified locally under `templates/memorial/` but is **not yet built in Figma**. Do not start that design until asked.
