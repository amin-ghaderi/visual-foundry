# Cursor Agent Rules

Read this file at the start of every design task in this repository.

Also read: `DESIGN_PROTOCOL.md`, `DESIGN_HANDOFF_PROTOCOL.md`, `config.yaml`.

If a project ID is known, read `projects/<ID>/project.yaml` and `projects/<ID>/LATEST.md`.

## Always do this, in order

1. **Read the project protocol** (`DESIGN_PROTOCOL.md`).
2. **Identify the project.** Use the given `PXXX` or create the next ID with `python pipeline/run.py create-project`. Never reuse IDs. Never invent an ID.
3. **Identify the input files.** Raw images belong in `projects/PXXX/input/`. Handoffs belong in `projects/PXXX/handoff/`.
4. **Interpret the Design Handoff.** Separate creative requirements from technical requirements. Fill missing technical values from `config.yaml` and the selected template. Do not invent creative content.
5. **Determine which pipeline stages are required** (background removal, refine, crop, upscale, Figma instance, export). Skip stages that are already satisfied by current validated assets.
6. **Prepare assets if needed** via `python pipeline/run.py prepare-image --project PXXX`. Run ComfyUI BiRefNet only when the cutout does not already exist. Never overwrite the original photograph.
7. **Use the correct template.** `templates/memorial/` for memorial work. Do not redesign the template. Populate it.
8. **Implement through Figma MCP.** Figma is the visual source of truth. Use native Figma objects. Create a fresh instance from the Master when the Master exists. Never copy P001 to make P002.
9. **Validate.** `python pipeline/run.py validate --project PXXX`.
10. **Export** the approved Figma frame into `projects/PXXX/exports/` with a deterministic name (`memorial-P001-v01.png`).
11. **Update project metadata** (`project.yaml`, `LATEST.md`, `figma/figma.yaml`).
12. **Report the final state** (`python pipeline/run.py status --project PXXX`).

## Never do this

- Redesign without instruction.
- Invent names, dates, slogans, quotes, symbols, or biography.
- Overwrite raw assets.
- Scatter generated files at the repo root.
- Create random folders.
- Use ambiguous filenames (`final-final.png`, `new-final.png`, `test-new.png`).
- Duplicate projects unnecessarily.
- Modify unrelated projects.
- Modify other MCP servers, MCP authentication, or `.cursor/mcp.json`.
- Reinstall ComfyUI or Python.
- Delete UNKNOWN files.
- Flatten a poster into one generated image.
- Derive a new person from another person's Figma file.
- Destroy **MCP TEST FRAME** or **PROJECT 03 — MCP TEST**.
- Start building the Figma Master Template unless the user asked for that work.

## MCP boundaries

- **Figma MCP** (`plugin-figma-figma`): design implementation only.
- **Comfy MCP** (`user-comfy-mcp`): local image preparation (BiRefNet) only.
- Do not re-auth, disconnect, or edit MCP config unless the user explicitly asks.

## Image engine

Reusable scripts live in `image-preparation/`. The orchestrator is `pipeline/prepare_image.py`. Prefer the CLI:

```text
python pipeline/run.py prepare-image --project P001
python pipeline/run.py status --project P001
```

Call the engine scripts directly only when debugging a single stage.

## Figma tracking

Write metadata to `projects/PXXX/figma/figma.yaml`:

- `figma_file_name`
- `figma_file_key`
- `figma_url`
- `frame_name`
- `frame_id`
- `template_used`
- `created_at`
- `updated_at`

Never store credentials.

## When information is missing

- Technical default exists in `config.yaml` or the template → use it.
- Creative fact is missing → leave blank / placeholder. Ask the user. Do not invent.
