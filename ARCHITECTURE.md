# Nano Banana — Architecture

**Version:** 1.3.0
**Repository:** https://github.com/flight505/nano-banana
**Author:** flight505 (Jesper Vang)

---

## Design Philosophy

1. **Zero Dependencies** — Python stdlib only (`urllib.request`), no PEP 668 issues
2. **Smart Iteration** — Threshold-based regeneration, not fixed iteration count
3. **Document-Type Awareness** — 13 quality presets for different output contexts
4. **Dual Provider** — Google Gemini API preferred, OpenRouter fallback
5. **Explicit Control** — Skills use `disable-model-invocation: true` to prevent unintended generation

---

## Provider Architecture

### Provider Auto-Detection

```
GEMINI_API_KEY set?  ──yes──→  Google Gemini API (direct, free tier)
        │no
OPENROUTER_API_KEY set?  ──yes──→  OpenRouter (multi-model)
        │no
        └→  Error: no API key found
```

Override with `--provider google` or `--provider openrouter`.

### Google Gemini API (Preferred)

- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}`
- **Image generation:** `generationConfig.responseModalities: ["TEXT", "IMAGE"]`
- **Image input:** `inlineData.mimeType` + `inlineData.data` (base64)
- **Response parsing:** `candidates[0].content.parts[]` — find `inlineData` for image, `text` for text
- **Models:** `gemini-3-pro-image-preview` (generation), `gemini-3-pro-preview` (review)
- **JPEG handling:** Google API may return JPEG for `.png` requests — auto-converted via `convert_to_png()`

### OpenRouter (Fallback)

- **Endpoint:** `https://openrouter.ai/api/v1/chat/completions`
- **Image generation:** `modalities: ["text", "image"]`
- **Image input:** `image_url.url` (data URI)
- **Response parsing:** `choices[0].message.content[]` — find `image_url` for image
- **Models:** `google/gemini-3-pro-image-preview`, `black-forest-labs/flux.2-pro`, `black-forest-labs/flux.2-flex`

---

## Three-Skill System

```
skills/
├── diagram/     → Technical diagrams with AI quality review + iteration
├── image/       → General image generation and editing
└── mermaid/     → Text-based diagrams (version-control friendly)
```

### Diagram Skill — Smart Iteration

**Core logic:** `skills/diagram/scripts/generate_diagram_ai.py` (`NanoBananaGenerator` class)

```
User prompt (+ optional --input image)
    ↓
Generate via Gemini API (image + text modalities)
    ↓
AI Quality Review (5 criteria, 0-2 pts each = 10 total)
    ↓
Score ≥ threshold? → Save and exit (early stop)
Score < threshold? → Build improved prompt from critique → Regenerate (max 2 iterations)
```

**Quality criteria:** Technical Accuracy, Clarity/Readability, Label Quality, Layout/Composition, Professional Appearance

**13 Document-Type Thresholds:**

| Threshold | Types |
|-----------|-------|
| 8.5 | `specification`, `journal` |
| 8.0 | `architecture`, `conference`, `proposal`, `thesis`, `grant` |
| 7.5 | `sprint`, `report`, `preprint`, `default` |
| 7.0 | `readme`, `poster` |
| 6.5 | `presentation` |

**Editing mode:** First iteration sends source image + edit prompt. Subsequent iterations refine from critique alone (no re-sending of original image).

### Image Skill

**Core logic:** `skills/image/scripts/generate_image.py`

- Single-pass generation (no quality review loop)
- Supports generation and editing via `--input` flag
- Importable as library — functions raise exceptions (`ValueError`, `RuntimeError`, `FileNotFoundError`), only `main()` calls `sys.exit()`

### Mermaid Skill

- Text-based diagrams rendered by GitHub, GitLab, Obsidian
- No API calls — pure markdown output
- 8 diagram types: flowchart, sequence, class, ERD, state, Gantt, pie, git graph

---

## Shared Utilities (`skills/common/`)

### `image_utils.py`

| Function | Purpose |
|----------|---------|
| `convert_to_png(data)` | Converts image bytes to PNG (PIL → sips → pass-through fallback) |
| `get_mime_type(path)` | Returns MIME type from file extension |
| `image_to_base64_url(path)` | Returns `data:{mime};base64,...` URI for a file |
| `MIME_TYPES` | Canonical extension → MIME type mapping |

### `env.py`

| Function | Purpose |
|----------|---------|
| `load_env_value(key)` | Searches `.env` files in cwd + up to 5 parent directories (stdlib only) |

These replace previously duplicated code across `generate_diagram_ai.py` and `generate_image.py`.

---

## Hook System

### PostToolUse Output Validation

**File:** `hooks/validate-output.py`
**Config:** `hooks/hooks.json`
**Event:** PostToolUse on Bash (5-second timeout)

**Activation:** Only fires for Bash commands containing `generate_image.py` or `generate_diagram`.

**Two-phase validation:**

1. **Error pattern matching** — Checks `tool_result` for known errors and provides targeted recovery guidance:
   - API key missing → "Run /nano-banana:setup"
   - HTTP 401/403 → "Check key"
   - HTTP 429 → "Rate limited, wait"
   - Timeout → "Try simpler prompt"
   - Missing source image → "Verify file path"

2. **Output file validation** — Parses `-o`/`--output` from command:
   - File exists
   - File size > 0
   - Valid PNG header (`.png` files)

---

## File Structure

```
nano-banana/
├── .claude-plugin/
│   └── plugin.json                  # Plugin manifest (v1.3.0)
├── .github/workflows/
│   └── notify-marketplace.yml       # Webhook to marketplace on version bump
├── assets/
│   └── nano-banana-hero-voxel.png   # Hero image
├── commands/
│   ├── edit.md                      # /nano-banana:edit command
│   └── setup.md                     # /nano-banana:setup command
├── hooks/
│   ├── hooks.json                   # PostToolUse hook declarations
│   └── validate-output.py           # Output validation + error recovery
├── skills/
│   ├── common/
│   │   ├── __init__.py              # Exports shared utilities
│   │   ├── env.py                   # Unified .env loading (stdlib)
│   │   └── image_utils.py           # PNG conversion, MIME types, base64
│   ├── diagram/
│   │   ├── SKILL.md                 # Diagram skill documentation
│   │   └── scripts/
│   │       ├── generate_diagram.py      # CLI wrapper (passes args through)
│   │       └── generate_diagram_ai.py   # NanoBananaGenerator class
│   ├── image/
│   │   ├── SKILL.md                 # Image skill documentation
│   │   └── scripts/
│   │       └── generate_image.py        # Image generation/editing
│   └── mermaid/
│       └── SKILL.md                 # Mermaid skill documentation
├── ARCHITECTURE.md                  # This file
├── CHANGELOG.md                     # Version history
├── CLAUDE.md                        # Developer instructions
├── LICENSE                          # MIT License
├── README.md                        # Public documentation
├── pyproject.toml                   # Python packaging (uv/pip)
└── requirements.txt                 # Empty (zero dependencies)
```

---

## Output Files

For diagram generation with output path `diagram.png`:
- `diagram_v1.png` — First iteration
- `diagram_v2.png` — Second iteration (if needed)
- `diagram.png` — Final version (copy of best)
- `diagram_review_log.json` — Quality scores and critiques

---

## Version History

### v1.3.0 (2026-02-20) — Current

- **Google Gemini API direct support** — preferred provider with free tier
- **Provider auto-detection** — `GEMINI_API_KEY` preferred, `OPENROUTER_API_KEY` fallback
- **`--provider` flag** on all scripts
- **Shared utilities** — `skills/common/image_utils.py` and `skills/common/env.py`
- **Error handling** — `generate_image.py` raises exceptions (importable as library)
- **JPEG-to-PNG conversion** — auto-convert when Google API returns JPEG
- **Deleted** unused `http_client.py` (OpenRouterClient class)

### v1.1.0 (2026-02-16)

- **`/nano-banana:edit` command** for iterative editing of existing images/diagrams
- **`--input` flag** on diagram and image scripts for editing
- **PostToolUse validation hook** — validates output files and provides error recovery
- **Skill hardening** — `disable-model-invocation: true` prevents unintended generation

### v1.0.3 (2025-01-08) — Zero Dependencies Rewrite

- Replaced `requests` library with `urllib.request` (stdlib only)
- Eliminated PEP 668 installation issues
- No `pip install` required

### v1.0.0 (2025-01-07) — Initial Release

- Extracted from [Claude Project Planner](https://github.com/flight505/claude-project-planner)
- Diagram skill with smart iteration and 13 document-type presets
- Image skill with generation and editing
- Mermaid skill for text-based diagrams

---

## Marketplace Integration

**Marketplace:** `flight505-marketplace` ([github.com/flight505/flight505-marketplace](https://github.com/flight505/flight505-marketplace))

Nano Banana is a git submodule. Version bumps auto-propagate via webhook:

```
Push to main (with version change in plugin.json)
    ↓  notify-marketplace.yml
repository_dispatch to flight505-marketplace
    ↓  auto-update-plugins.yml (~30 seconds)
marketplace.json updated + submodule pointer advanced
```

**Bump command:** `../../scripts/bump-plugin-version.sh nano-banana X.Y.Z`

---

## Technical Constraints

- **Python 3.8+** minimum (f-strings, type hints, urllib.request modern API)
- **Internet required** for all generation (API calls)
- **No vector output** (SVG tested Feb 2026, quality far inferior to raster — revisit when image models can natively output vector)
- **PNG output only** for generation (base64 decoded from API response)
- **Max 2 iterations** for diagram quality review loop

---

**Document Version:** 3.0.0
**Last Updated:** 2026-02-20
