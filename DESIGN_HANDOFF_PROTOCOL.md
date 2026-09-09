# Design Handoff Protocol

Contract between ChatGPT (Art Director) and Cursor (Execution Agent).

ChatGPT does **not** need to know Cursor, Python, ComfyUI, Figma MCP, APIs, or file paths.

Cursor is responsible for translating creative intent into technical execution.

## What ChatGPT should provide

Any reasonable combination of:

- A short design brief in natural language
- Structured Markdown or JSON
- Names and dates (only real ones)
- Memorial text the family/editor actually approved
- A raw photograph
- Reference images
- A template name (`memorial`)
- Notes about what must not change

ChatGPT should **not** write Python, Comfy graphs, or Figma plugin code.

## Suggested handoff shape (optional)

Cursor accepts messy input. This shape is helpful when available, not required:

```markdown
# Design Handoff

Template: memorial
Project: (new | P001)

## Objective
One sentence.

## Canvas
1080 × 1920 (omit to use the template default)

## Content
- Persian name:
- English name:
- Birth year:
- Death year:
- Location:
- Identifier:
- Statement (FA):
- Statement (EN):
- Biography (FA):
- Biography (EN):

## Imagery
Attach or name the original photograph.
Image treatment: cutout on black portrait well, no retouch.

## Restrictions
Do not invent facts.
Do not change the template geometry.
```

JSON using `templates/memorial/PERSON_SCHEMA.json` is also valid.

## What Cursor extracts

Creative requirements:

- objective
- composition / hierarchy intent
- typography intent (if stated)
- color intent (if stated)
- imagery and image treatment
- content fields
- references
- restrictions
- requested changes

Technical requirements:

- canvas size
- template
- spacing / alignment (if stated)
- export size
- whether background removal, refine, crop, or upscale is needed

If a technical value is missing, Cursor uses `config.yaml` and the template. Cursor never invents creative content.

## Template rule

If the handoff says `template: memorial`, load `templates/memorial/` and **populate** it.

If no template is named and the user asks for a **new** design, write a new spec. Do not mutate an unrelated template.

## Files Cursor writes

For project `PXXX`:

| File | Role |
|---|---|
| `projects/PXXX/handoff/handoff-v01.md` | Original handoff text as received |
| `projects/PXXX/handoff/interpreted-v01.yaml` | Cursor's extraction (no invented facts) |
| `projects/PXXX/input/` | Original photograph(s) |
| `projects/PXXX/project.yaml` | Current version pointers |

## Empty fields

An empty name, date, quote, or biography stays empty.

Cursor must not fill gaps with sample copy, “lorem”, or guessed biography.
