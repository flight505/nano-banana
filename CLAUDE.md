# Nano Banana - Claude Code Plugin Instructions

AI-powered image, diagram, and video generation for Claude Code using Nano Banana 2 (fast), Nano Banana Pro (quality), and Veo 3.1 (video) via Google Gemini API.

## Version Management & Marketplace Sync

**Files to update on every version bump:**

| File | What to change |
|------|---------------|
| `.claude-plugin/plugin.json` | `"version"` field |
| `pyproject.toml` | `version =` field |
| `README.md` | Version badge (`version-X.Y.Z-blue`) |
| `ARCHITECTURE.md` | `**Version:**` header + version history |
| `CHANGELOG.md` | Add new entry (for meaningful releases) |

**Workflow:**

1. Update all files above
2. **Commit & push** to trigger webhook: `git commit -m "chore: bump version to X.Y.Z" && git push`
3. **Verify webhook** fired (5 sec): `gh run list --repo flight505/nano-banana --limit 1`
4. **Marketplace auto-syncs** within 30 seconds — no manual `marketplace.json` update needed

**Tip**: The bump script handles `plugin.json` and `README.md` badge only. You must manually update `pyproject.toml`, `ARCHITECTURE.md`, and `CHANGELOG.md`.

```bash
../../scripts/bump-plugin-version.sh nano-banana X.Y.Z
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `/nano-banana:setup` | Configure API keys and environment |
| `/nano-banana:edit` | Edit an existing image or diagram with AI |

## Skills

| Skill | Description | Default Model |
|-------|-------------|---------------|
| `diagram` | Generate technical diagrams with AI quality review and smart iteration | Nano Banana Pro (`gemini-3-pro-image-preview`) |
| `visual-abstract` | Create Nature-quality scientific figures with visual metaphors and isometric depth | Nano Banana Pro (`gemini-3-pro-image-preview`) |
| `image` | Generate and edit images using AI models | Nano Banana 2 (`gemini-3.1-flash-image-preview`) |
| `video` | Generate videos using Veo 3.1 | `veo-3.1-fast-generate-preview` |
| `kroki` | Render text-based diagrams (Mermaid, PlantUML, GraphViz, D2, etc.) to PNG/SVG | Kroki.io (free) |

## Usage

### Generate a Diagram

```bash
python3 skills/diagram/scripts/generate_diagram.py "description" -o output.png --doc-type TYPE --style STYLE
```

**Style Presets:** `technical` (default), `visual-abstract`, `minimal`

**Document Types:** `specification`, `architecture`, `proposal`, `journal`, `conference`, `thesis`, `grant`, `sprint`, `report`, `preprint`, `readme`, `poster`, `presentation`, `default`

### Generate an Image

```bash
python3 skills/image/scripts/generate_image.py "description" -o output.png

# With aspect ratio and resolution
python3 skills/image/scripts/generate_image.py "description" -o output.png --aspect-ratio 16:9 --resolution 2K

# Use Nano Banana Pro for highest quality
python3 skills/image/scripts/generate_image.py "description" -o output.png -m gemini-3-pro-image-preview
```

### Generate a Video

```bash
python3 skills/video/scripts/generate_video.py "description" -o output.mp4

# Image-to-video (animate a still image)
python3 skills/video/scripts/generate_video.py "description" --input source.png -o output.mp4
```

### Edit an Image or Diagram

```bash
python3 skills/image/scripts/generate_image.py "edit instructions" --input source.png -o output.png
python3 skills/diagram/scripts/generate_diagram.py "edit instructions" --input source.png -o output.png --doc-type architecture
```

## Requirements

- **GEMINI_API_KEY** environment variable
- **google-genai** Python SDK (`uv sync` or `pip install google-genai`)
- Python 3.10+
- **ffmpeg** (optional, for video audio stripping)

## When to Use Which Skill

- **Technical diagrams from description** (architecture, flowcharts, ERD) → `diagram` skill
- **Publication-quality scientific figures** (visual metaphors, README heroes, Nature-style) → `visual-abstract` skill
- **Creative images** (photos, art, illustrations) → `image` skill
- **Video content** (demos, animations, transitions) → `video` skill
- **Render diagram source code** (Mermaid, PlantUML, DOT, D2) → `kroki` skill

## Key Principles

1. **google-genai SDK** — single SDK for all Gemini and Veo models
2. **Style presets via `system_instruction`** — aesthetics separated from content (`--style technical|visual-abstract|minimal`)
3. **Multi-turn chat iteration** — diagram refinement uses `client.chats.create()` for context-aware improvement
4. **Smart iteration** — diagram skill only regenerates if quality below threshold
5. **Document-type aware** — 13 quality thresholds for different output contexts
6. **AI review** — Gemini 3.1 Pro reviews each diagram generation
7. **Shared utilities** — `skills/common/` provides presets, client, image utils, and env helpers
