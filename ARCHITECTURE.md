# Nano Banana — Architecture

**Version:** 3.0.2
**Repository:** https://github.com/flight505/nano-banana
**Author:** flight505 (Jesper Vang)

---

## Design Philosophy

1. **google-genai SDK** — single SDK for all Gemini and Veo models (replaces urllib.request)
2. **Smart Iteration** — Threshold-based regeneration, not fixed iteration count
3. **Document-Type Awareness** — 13 quality presets for different output contexts
4. **Single Provider** — Google Gemini API only (no fallback chain)
5. **Explicit Control** — Skills use `disable-model-invocation: true` to prevent unintended generation

---

## Provider Architecture

### SDK Migration (v3.0.0)

All skills now use the `google-genai` Python SDK instead of raw `urllib.request` calls. The shared client factory in `skills/common/client.py` creates and configures the client from `GEMINI_API_KEY`.

### Model Hierarchy

| Name | Model ID | Speed | Use Case |
|------|----------|-------|----------|
| **Nano Banana 2** | `gemini-3.1-flash-image-preview` | Flash (fastest) | High-volume, general use (image skill default) |
| **Nano Banana Pro** | `gemini-3-pro-image-preview` | Pro | Professional assets, best quality (diagram skill default) |
| **Veo 3.1 Fast** | `veo-3.1-fast-generate-preview` | Fast | Video generation (video skill default) |
| **Veo 3.1** | `veo-3.1-generate-preview` | Standard | High-quality video generation |
| **Review** | `gemini-3.1-pro-preview` | Pro | AI quality review (diagram skill) |

### Google Gemini API (via google-genai SDK)

- **SDK:** `google-genai` Python package
- **Client factory:** `skills/common/client.py` — shared `google.genai.Client` instance
- **Image generation:** `client.models.generate_content()` with `response_modalities=["TEXT", "IMAGE"]`
- **Video generation:** `client.models.generate_videos()` with Veo 3.1 models
- **Image config:** `generationConfig.imageConfig: { aspectRatio, imageSize }`
- **Aspect ratios:** 1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9
- **Image sizes:** 512px, 1K, 2K, 4K
- **JPEG handling:** API may return JPEG for `.png` requests — auto-converted via `convert_to_png()`

---

## Four-Skill System

```
skills/
├── diagram/     → AI-generated technical diagrams with quality review + iteration
├── image/       → General image generation and editing
├── video/       → Veo 3.1 text-to-video, image-to-video, frame interpolation, video extension
└── kroki/       → Render text-based diagrams (27 types) to PNG/SVG via Kroki.io
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

### Video Skill

**Core logic:** `skills/video/scripts/generate_video.py`

- Text-to-video and image-to-video generation via Veo 3.1
- Frame interpolation and video extension modes
- Optional ffmpeg audio stripping for clean output
- Default model: `veo-3.1-fast-generate-preview` (fast), `veo-3.1-generate-preview` (quality)

### Kroki Skill

**Core logic:** `skills/kroki/scripts/render_diagram.py`

- Renders text-based diagram source (Mermaid, PlantUML, GraphViz, D2, etc.) to PNG/SVG/PDF via [Kroki.io](https://kroki.io)
- 27 diagram types supported (see `--list-types`)
- POST request with JSON body: `{"diagram_source": "...", "diagram_type": "mermaid", "output_format": "png"}`
- Reads from file (`--input`), inline (`--source`), or stdin
- Supports self-hosted Kroki via `--server`
- Only triggers when user explicitly asks for text-based diagram rendering

---

## Shared Utilities (`skills/common/`)

### `client.py`

| Function | Purpose |
|----------|---------|
| `get_client()` | Returns a configured `google.genai.Client` using `GEMINI_API_KEY` |

Shared client factory used by image, diagram, and video skills. Loads API key from environment or `.env` files via `env.py`.

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
│   └── plugin.json                  # Plugin manifest
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
│   │   ├── client.py                # google-genai client factory
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
│   ├── video/
│   │   ├── SKILL.md                 # Video skill documentation
│   │   └── scripts/
│   │       └── generate_video.py        # Veo 3.1 video generation
│   └── kroki/
│       ├── SKILL.md                 # Kroki skill documentation
│       └── scripts/
│           └── render_diagram.py        # Kroki.io rendering (27 types)
├── ARCHITECTURE.md                  # This file
├── CHANGELOG.md                     # Version history
├── CLAUDE.md                        # Developer instructions
├── LICENSE                          # MIT License
├── README.md                        # Public documentation
├── pyproject.toml                   # Python packaging (uv/pip)
└── requirements.txt                 # google-genai>=1.0.0
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

### v3.0.1 (2026-03-12) — Current

- **Fix:** Video resolution now passed to `GenerateVideosConfig` (was silently ignored)
- **Fix:** Removed unsupported 4K video resolution (SDK only supports 720p/1080p)
- **Fix:** Reference images use native `VideoGenerationReferenceImage` SDK type
- **Fix:** Native `generate_audio` flag added (ffmpeg kept as backup)
- **Fix:** Stale model ID `gemini-3-pro-image-preview` → `gemini-3-pro-image-preview`
- **Fix:** Defensive `response.text` access in diagram review
- **Fix:** `requires-python` corrected to `>=3.10`
- Removed dead code (`save_base64_image`, `import base64`)

### v3.0.0 (2026-03-12)

- **Breaking:** Dropped OpenRouter provider support — Google Gemini API only
- **Breaking:** Requires `google-genai` Python SDK (replaces `urllib.request`)
- **Breaking:** Model IDs updated to 3.1 versions
- **Video generation skill** — Veo 3.1 text-to-video, image-to-video, frame interpolation, video extension
- **Shared client factory** — `skills/common/client.py` for google-genai SDK
- Default image model: `gemini-3.1-flash-image-preview`
- Default diagram model: `gemini-3-pro-image-preview`
- ffmpeg audio stripping for generated videos

### v2.0.0 (2026-03-02)

- **Breaking:** Default image model changed from `gemini-3-pro-image-preview` to `gemini-3.1-flash-image-preview` (Nano Banana 2)
- **Diagram skill** keeps `gemini-3-pro-image-preview` (Nano Banana Pro) for highest quality
- **`imageConfig` support** — aspect ratio and resolution control via `--aspect-ratio` and `--resolution` flags
- **New CLI args:** `--aspect-ratio` (14 ratios) and `--resolution` (512px, 1K, 2K, 4K)
- **Replaced mermaid skill with kroki skill** — renders 27 diagram types (Mermaid, PlantUML, GraphViz, D2, etc.) to PNG/SVG via Kroki.io
- Removed deprecated `gemini-2.5-flash-image-preview` references

### v1.3.2 (2026-02-24)

- Fix OpenRouter 401 when `--provider openrouter` with both API keys set
- Fix OpenRouter images saved as JPEG instead of PNG
- Correct API key routing per explicit `--provider` flag

### v1.3.1 (2026-02-20)

- Documentation consolidation (ARCHITECTURE.md replaces CONTEXT_nano-banana.md)
- Removed stale docs/plans/ implementation plans
- Updated CLAUDE.md and README.md for v1.3.0 changes

### v1.3.0 (2026-02-20)

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

- **Python 3.10+** minimum (google-genai SDK requirement)
- **Internet required** for all generation (API calls)
- **No vector output** (SVG tested Feb 2026, quality far inferior to raster — revisit when image models can natively output vector)
- **PNG output only** for generation (base64 decoded from API response)
- **Max 2 iterations** for diagram quality review loop

---

**Last Updated:** 2026-03-12
