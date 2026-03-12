# Nano Banana v3.0.0 — Video Skill & SDK Migration

**Date:** 2026-03-12
**Author:** Jesper Vang (@flight505)
**Status:** Approved

---

## Overview

Add video generation to Nano Banana using Google Veo 3.1 via the Gemini API, and migrate the entire plugin from raw `urllib.request` to the `google-genai` Python SDK. Drop OpenRouter support.

### Why

The key value of Nano Banana as a Claude Code plugin is the integrated flow — Claude reads project context (JSON, architecture docs, code) and generates contextually-aware prompts. Video generation via Veo 3.1 extends this to animated content: website hero backgrounds, animated presentations, slide transitions, product demos. The Gemini UI is cheaper but creates a disconnect; the plugin keeps everything in one workflow.

### Breaking Changes (v3.0.0)

- `google-genai` SDK required (no longer zero-deps)
- OpenRouter support removed (`--provider` flag gone, `OPENROUTER_API_KEY` ignored)
- FLUX models no longer available
- Diagram default model changes from `gemini-3-pro-image-preview` to `gemini-3.1-pro-image-preview`
- `GEMINI_API_KEY` on paid tier required for video generation

---

## Architecture

### SDK Migration

Replace all `urllib.request` API calls with `google-genai` SDK across the entire plugin.

**New shared client** (`skills/common/client.py`):

```python
from google import genai
from common.env import load_env_value

def get_client() -> genai.Client:
    """Return a configured Gemini client.

    Checks GEMINI_API_KEY env var, then .env files.
    Raises ValueError if no key found.
    """
    key = os.getenv("GEMINI_API_KEY") or load_env_value("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY not found.\n"
            "Set: export GEMINI_API_KEY=your-key\n"
            "Get one at: https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=key)
```

Every skill imports `get_client()` instead of constructing HTTP requests.

**What gets deleted:**
- `_resolve_provider()` — no more auto/google/openrouter switching
- `_generate_via_openrouter()` in `generate_image.py`
- `--provider` flag from all CLI scripts
- All `urllib.request` API construction code
- OpenRouter-specific headers, response parsing, model name mapping

**What stays:**
- `image_utils.py` — still needed for PNG conversion, MIME types
- `env.py` — still loads `.env` files for the API key
- CLI interfaces (argparse) — same flags minus `--provider`
- Error handling — map SDK exceptions to user-friendly messages

### Model Updates

| Skill | Old Default | New Default |
|-------|-------------|-------------|
| Image | `gemini-3.1-flash-image-preview` | `gemini-3.1-flash-image-preview` (unchanged) |
| Diagram (generation) | `gemini-3-pro-image-preview` | `gemini-3.1-pro-image-preview` |
| Diagram (review) | `gemini-3-pro-preview` | `gemini-3.1-pro-preview` |
| Video (default) | N/A | `veo-3.1-fast-generate-preview` |
| Video (quality) | N/A | `veo-3.1-generate-preview` |

Only Veo 3.1 models are included. Veo 2 and Veo 3 are being sunset.

---

## Video Skill Design

### File Structure

```
skills/video/
├── SKILL.md
└── scripts/
    ├── __init__.py
    └── generate_video.py
```

### SKILL.md Frontmatter (Skill 2.0)

```yaml
---
name: video
description: "Generate videos using Veo 3.1 via Google Gemini API. Supports text-to-video,
  image-to-video animation, frame interpolation between two images, video extension,
  and reference image guidance. Use when the user needs animated content, video assets,
  motion graphics, slide transitions, hero animations, or wants to animate an existing
  image or diagram. Pairs with the image and diagram skills for an image-to-video pipeline."
argument-hint: "[description or instruction]"
allowed-tools: [Read, Write, Edit, Bash]
disable-model-invocation: true
---
```

Uses `${CLAUDE_SKILL_DIR}` for script path references in the body.

### CLI Interface

```
generate_video.py <prompt> [options]
```

| Flag | Purpose | Default |
|------|---------|---------|
| `prompt` (positional) | Text description of the video | required |
| `-o, --output` | Output file path (.mp4) | `generated_video.mp4` |
| `-m, --model` | Model ID | `veo-3.1-fast-generate-preview` |
| `-i, --input` | Input image (image-to-video) | None |
| `--last-frame` | Last frame image (interpolation) | None |
| `--extend` | Video to extend (extension mode) | None |
| `--reference` | Reference images, repeatable, max 3 | None |
| `--aspect-ratio` | `16:9` or `9:16` | `16:9` |
| `--resolution` | `720p`, `1080p`, `4k` | `720p` |
| `--duration` | `4`, `6`, `8` seconds | `8` |
| `--audio` | Keep audio track (opt-in) | Strip audio |
| `--timeout` | Max poll time in seconds | `360` |

### Mode Detection

Automatic from flags, no explicit `--mode` needed:

| Flags Present | Mode |
|--------------|------|
| `--extend` | Video extension |
| `--input` + `--last-frame` | Frame interpolation |
| `--input` only | Image-to-video |
| Neither | Text-to-video |

### Core Flow

```
Parse args → detect mode → validate constraints → get_client()
    ↓
client.models.generate_videos(model, prompt, config, image?, video?)
    ↓
Poll operation (sleep 10s, print progress)
    ↓
client.files.download(video) → save to temp path
    ↓
--audio absent? → ffmpeg -i temp.mp4 -an -c:v copy output.mp4
--audio present? → mv temp.mp4 output.mp4
    ↓
Print: "Video saved to: {path} ({duration}s, {resolution})"
```

### Audio Handling

Veo 3.1 generates audio by default (dialogue, SFX, ambient). There is no API parameter to disable it.

- **Default behavior:** Strip audio post-generation via `ffmpeg -i input.mp4 -an -c:v copy output.mp4`
- **Opt-in:** Pass `--audio` to keep the audio track
- **Graceful degradation:** If `ffmpeg` not found (`shutil.which("ffmpeg")` returns None), save with audio and warn: "Install ffmpeg to strip audio from generated videos"

Audio is opt-in because the primary use cases (website assets, animated presentations, looping backgrounds) don't need audio, and it increases file size.

### Constraint Validation

The script validates Veo API constraints before making the call:

| Constraint | Rule | Error Message |
|-----------|------|---------------|
| 1080p/4K duration | Must be 8 seconds | "1080p and 4K resolution require --duration 8" |
| Extension resolution | Must be 720p | "Video extension only supports 720p resolution" |
| Reference images | Max 3 | "Maximum 3 reference images allowed" |
| Extension input | Must be .mp4 | "Extension requires an .mp4 video file" |
| Aspect ratio | Only 16:9 or 9:16 | "Video supports 16:9 or 9:16 aspect ratios only" |

### Resolution and Pricing

| Resolution | Duration | Price/clip (Fast) | Price/clip (Standard) |
|------------|----------|-------------------|-----------------------|
| 720p | 4s | $0.60 | $1.60 |
| 720p | 6s | $0.90 | $2.40 |
| 720p | 8s | $1.20 | $3.20 |
| 1080p | 8s | $1.20 | $3.20 |
| 4K | 8s | $2.80 | $4.80 |

---

## Key Use Cases

### Image-to-Video Pipeline

Generate a still with existing Nano Banana skills, then animate:

```bash
# Step 1: Generate architecture diagram
python3 ${CLAUDE_SKILL_DIR}/../diagram/scripts/generate_diagram.py "microservice architecture" -o arch.png

# Step 2: Animate it
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "Camera slowly zooms in, components light up sequentially" --input arch.png -o arch_animated.mp4
```

Claude Code handles this chaining naturally — it reads the project context, generates the image, then animates it.

### Frame Interpolation (Slide Transitions)

```bash
# Generate two slide visuals, then create a smooth transition
python3 generate_video.py "Smooth morphing transition between slides" \
  --input slide1.png --last-frame slide2.png -o transition.mp4
```

### Website Hero Animation

```bash
# Silent looping background video
python3 generate_video.py "Abstract particles flowing in dark space, subtle blue glow" \
  -o hero_bg.mp4 --aspect-ratio 16:9 --resolution 1080p
```

### Video with Audio

```bash
# Product demo with narration
python3 generate_video.py "A narrator says: 'Welcome to our platform.' \
  Camera pans across a modern dashboard interface." \
  -o intro.mp4 --audio -m veo-3.1-generate-preview
```

---

## File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `skills/common/client.py` | Shared `google-genai` client factory |
| `skills/video/SKILL.md` | Video skill documentation (Skill 2.0) |
| `skills/video/scripts/__init__.py` | Package init |
| `skills/video/scripts/generate_video.py` | Video generation script |

### Modified Files

| File | Changes |
|------|---------|
| `skills/image/scripts/generate_image.py` | Rewrite to use SDK, remove OpenRouter |
| `skills/diagram/scripts/generate_diagram_ai.py` | Rewrite to use SDK, update model IDs |
| `skills/diagram/scripts/generate_diagram.py` | Update for SDK |
| `skills/image/SKILL.md` | Remove OpenRouter references, update ${CLAUDE_SKILL_DIR} |
| `skills/diagram/SKILL.md` | Update model references |
| `.claude-plugin/plugin.json` | Add video skill, update keywords, description |
| `pyproject.toml` | Add `google-genai` dependency, bump to 3.0.0 |
| `requirements.txt` | Add `google-genai` |
| `hooks/validate-output.py` | Extend for .mp4 validation |
| `commands/setup.md` | Remove OpenRouter setup, note paid tier for video |
| `CLAUDE.md` | Add video skill docs, update provider info |
| `ARCHITECTURE.md` | Document video skill, SDK migration, v3.0.0 |
| `README.md` | Add video skill, update requirements |
| `CHANGELOG.md` | v3.0.0 entry |

### Deleted Code

| What | Where |
|------|-------|
| `_resolve_provider()` | `generate_image.py` |
| `_generate_via_openrouter()` | `generate_image.py` |
| `--provider` argument | All CLI scripts |
| OpenRouter headers/parsing | Throughout |

---

## Post-Build

1. **Verify exact model IDs** — Confirm `gemini-3.1-pro-image-preview` is the correct ID for the new diagram model
2. **Run skill-creator eval loop** — Optimize the video skill description for triggering accuracy
3. **Test all modes** — text-to-video, image-to-video, interpolation, extension, reference images
4. **Test SDK migration** — Verify image and diagram skills still work identically
5. **Version bump** — 3.0.0 across plugin.json, pyproject.toml, README badge, ARCHITECTURE.md

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `google-genai` | latest | Google Gemini API SDK |
| `ffmpeg` (system) | any | Audio stripping (optional, graceful fallback) |

Python stdlib remains for everything else (argparse, pathlib, base64, etc.).
