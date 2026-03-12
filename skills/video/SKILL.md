---
name: video
description: "Generate videos using Veo 3.1 — text-to-video, image-to-video, frame interpolation, and video extension"
argument-hint: "[description or instruction]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
disable-model-invocation: true
---

# Nano Banana - Video Generation

## Overview

Generate videos using Google's Veo 3.1 models via the google-genai SDK. Supports four generation modes: text-to-video, image-to-video, frame interpolation, and video extension.

**Key Features:**
- Four generation modes from a single script
- Fast (default) and standard quality models
- Aspect ratio control (16:9, 9:16)
- Resolution up to 1080p
- Configurable duration (4, 6, or 8 seconds)
- Automatic audio stripping (opt-in to keep)
- Reference images for style guidance

## When to Use This Skill

Use this skill when you need:

- **Animated content** from a text description
- **Image animation** — bring a still photo or illustration to life
- **Smooth transitions** between two frames (interpolation)
- **Extending** an existing video clip
- **Short-form video** for reels, demos, or presentations

**Not for:** Static images (use `image` skill), technical diagrams (use `diagram` skill), or diagram source rendering (use `kroki` skill).

## Quick Start

### Text-to-Video (default)

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "A drone flyover of a coastal city at golden hour" -o flyover.mp4
```

### Image-to-Video

Animate a still image with a motion prompt:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "Camera slowly zooms in while clouds drift" \
  --input photo.png -o animated.mp4
```

### Frame Interpolation

Generate a smooth transition between two frames:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "Smooth morph between scenes" \
  --input start.png --last-frame end.png -o transition.mp4
```

### Video Extension

Continue an existing video clip:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "The camera keeps panning right revealing more of the landscape" \
  --extend clip.mp4 -o extended.mp4
```

### With Reference Images

Guide the visual style with up to 3 reference images:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "A cat walking through a garden" \
  -o styled.mp4 --reference style1.png --reference style2.png
```

## Models

| Model | ID | Speed | Best For |
|-------|-----|-------|----------|
| **Veo 3.1 Fast** | `veo-3.1-fast-generate-preview` | Fast | Default — quick iterations, drafts |
| **Veo 3.1** | `veo-3.1-generate-preview` | Standard | Final output, higher quality |

Use `-m` to select a model:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "A sunset timelapse" -o sunset.mp4 -m veo-3.1-generate-preview
```

## Resolution and Duration Constraints

| Resolution | Supported Durations | Notes |
|------------|-------------------|-------|
| **720p** (default) | 4, 6, 8 seconds | All durations, required for extension |
| **1080p** | 8 seconds only | Higher quality, duration locked |

```bash
# 720p, 4 seconds (fast preview)
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "Quick test" -o test.mp4 --resolution 720p --duration 4

# 1080p, must be 8 seconds
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "Cinematic landscape" -o landscape.mp4 --resolution 1080p --duration 8
```

**Constraint rules:**
- `--resolution 1080p` requires `--duration 8`
- `--extend` requires `--resolution 720p`
- Maximum 3 `--reference` images

## Aspect Ratio

| Ratio | Use Case |
|-------|----------|
| **16:9** (default) | Landscape, presentations, YouTube |
| **9:16** | Portrait, mobile reels, TikTok, Stories |

```bash
# Vertical video for social media
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "A vertical reel of a coffee being poured" \
  -o reel.mp4 --aspect-ratio 9:16
```

## Audio Handling

By default, audio is **stripped** from generated videos using ffmpeg. This avoids unexpected AI-generated audio.

```bash
# Default: audio stripped
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "A beach scene" -o beach.mp4

# Keep generated audio
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "A concert crowd cheering" -o concert.mp4 --audio
```

**Requirements for audio stripping:**
- `ffmpeg` must be installed (`brew install ffmpeg` on macOS)
- If ffmpeg is not found, the video is saved with audio intact and a warning is printed

## All CLI Flags

| Flag | Default | Description |
|------|---------|-------------|
| `prompt` (positional) | *required* | Text description of the video |
| `-o / --output` | *required* | Output .mp4 file path |
| `-m / --model` | `veo-3.1-fast-generate-preview` | Model ID |
| `-i / --input` | — | Input image (image-to-video / interpolation) |
| `--last-frame` | — | Last frame image (interpolation, requires --input) |
| `--extend` | — | Video .mp4 to extend |
| `--reference` | — | Reference image (repeatable, max 3) |
| `--aspect-ratio` | `16:9` | `16:9` or `9:16` |
| `--resolution` | `720p` | `720p` or `1080p` |
| `--duration` | `8` | `4`, `6`, or `8` seconds |
| `--audio` | off | Keep generated audio |
| `--timeout` | `360` | Max wait in seconds |
| `--api-key` | — | Override GEMINI_API_KEY |

## Configuration

### API Key Setup

```bash
export GEMINI_API_KEY='your-key-here'
```

Get a key at [https://aistudio.google.com/apikey](https://aistudio.google.com/apikey).

Or add to a `.env` file in your project:

```
GEMINI_API_KEY=your-key-here
```

Run `/nano-banana:setup` for guided configuration.

## Tips for Better Videos

### Be Descriptive About Motion

```bash
# Vague — model guesses camera movement
"A mountain"

# Specific — clear motion intent
"A slow aerial drone shot pulling back from a snowy mountain peak, revealing the valley below, golden hour lighting"
```

### Specify Camera Movement

Use terms like: pan left/right, zoom in/out, dolly, orbit, tracking shot, crane shot, steady cam, timelapse.

### For Image-to-Video, Describe the Animation

```bash
# Good: describes what should move
python3 ${CLAUDE_SKILL_DIR}/scripts/generate_video.py "The clouds slowly drift across the sky while the water gently ripples" \
  --input landscape.png -o animated.mp4
```

## Troubleshooting

### "No Gemini API key found"
Set the `GEMINI_API_KEY` environment variable or create a `.env` file. Run `/nano-banana:setup` for help.

### "Constraint validation failed"
Check the resolution/duration constraint table above. Common issue: using `--resolution 1080p` with `--duration 4`.

### Generation Timeout
Default timeout is 360 seconds (6 minutes). Video generation typically takes 1-4 minutes. Increase with `--timeout 600` for complex prompts.

### "ffmpeg not found" Warning
Install ffmpeg for automatic audio stripping: `brew install ffmpeg`. Without it, videos are saved with AI-generated audio.

### Video Appears Black or Corrupted
Try a simpler prompt, or switch to the standard quality model (`-m veo-3.1-generate-preview`). Some complex scenes may not render well at lower quality settings.

## Comparison: video vs image vs diagram

| Aspect | `video` | `image` | `diagram` |
|--------|---------|---------|-----------|
| **Output** | .mp4 video | .png image | .png diagram |
| **Models** | Veo 3.1 | Gemini Flash/Pro | Gemini Pro |
| **Duration** | 4-8 seconds | Instant | 1-2 passes |
| **Editing** | Extend existing | Edit existing | Edit existing |
| **Best For** | Animation, motion | Photos, art | Architecture, flowcharts |
