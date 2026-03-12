# Nano Banana v3.0.0 Implementation Plan

> **For Claude:** Execute this plan task-by-task using TDD. For parallel execution, the user can run `/batch` with this plan file.

**Goal:** Add Veo 3.1 video generation skill and migrate entire plugin from urllib.request to google-genai SDK, dropping OpenRouter.

**Architecture:** Shared `get_client()` factory in `skills/common/client.py`. Each skill uses the SDK directly. Video skill follows same pattern as image/diagram (single script, CLI flags, argparse). Audio stripped by default via ffmpeg.

**Tech Stack:** Python 3.8+, google-genai SDK, ffmpeg (optional, for audio stripping)

**Design doc:** `docs/plans/2026-03-12-video-skill-and-sdk-migration-design.md`

---

### Task 1: Add google-genai dependency and install

**Files:**
- Modify: `pyproject.toml:38-40`
- Modify: `requirements.txt`

**Step 1: Update pyproject.toml dependencies**

In `pyproject.toml`, replace:
```python
dependencies = [
    # No required dependencies - uses Python stdlib only
]
```
With:
```python
dependencies = [
    "google-genai>=1.0.0",
]
```

Also remove `"openrouter"` from the keywords list at line 17.

**Step 2: Update requirements.txt**

Replace empty `requirements.txt` with:
```
google-genai>=1.0.0
```

**Step 3: Install the dependency**

Run: `uv sync`
Expected: google-genai installs successfully

**Step 4: Verify import works**

Run: `uv run python -c "from google import genai; print('google-genai OK')"`
Expected: `google-genai OK`

**Step 5: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "chore: add google-genai SDK dependency"
```

---

### Task 2: Create shared client factory

**Files:**
- Create: `skills/common/client.py`
- Modify: `skills/common/__init__.py`
- Test: verify import works

**Step 1: Write skills/common/client.py**

```python
"""Shared Google Gemini client for Nano Banana skills."""

import os
from typing import Optional

from google import genai

from common.env import load_env_value


def get_client(api_key: Optional[str] = None) -> genai.Client:
    """Return a configured Gemini API client.

    Resolution order:
    1. Explicit api_key parameter
    2. GEMINI_API_KEY environment variable
    3. GEMINI_API_KEY from .env files (via load_env_value)

    Raises:
        ValueError: If no API key is found.
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or load_env_value("GEMINI_API_KEY")
    if not key:
        raise ValueError(
            "GEMINI_API_KEY not found.\n\n"
            "Set one of:\n"
            "  export GEMINI_API_KEY=your-key\n"
            "  Add GEMINI_API_KEY=your-key to a .env file\n\n"
            "Get a key at: https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=key)
```

**Step 2: Update skills/common/__init__.py**

Replace contents with:
```python
"""Shared utilities for Nano Banana skills."""
```

**Step 3: Verify the import chain**

Run: `cd skills && uv run python -c "import sys; sys.path.insert(0, '.'); from common.client import get_client; print('client OK')"`
Expected: `client OK`

**Step 4: Commit**

```bash
git add skills/common/client.py skills/common/__init__.py
git commit -m "feat: add shared google-genai client factory"
```

---

### Task 3: Migrate image skill to SDK

**Files:**
- Modify: `skills/image/scripts/generate_image.py` (full rewrite)
- Modify: `skills/image/SKILL.md` (remove OpenRouter references)

**Step 1: Rewrite generate_image.py**

Replace the entire file. Key changes:
- Import `get_client` from `common.client`
- Remove `_resolve_provider()`, `_generate_via_openrouter()`, `_generate_via_google()` (all 3 functions)
- Remove `--provider` argument from argparse
- Remove all `urllib.request`, `urllib.error`, `socket` imports
- Use `client.models.generate_content()` from the SDK
- Keep `save_base64_image()`, `calculate_aspect_ratio()` helpers
- Keep `image_utils` imports for PNG conversion

Core generation function using SDK:

```python
from google.genai import types

def generate_image(
    prompt: str,
    model: str = "gemini-3.1-flash-image-preview",
    output_path: str = "generated_image.png",
    api_key: Optional[str] = None,
    input_image: Optional[str] = None,
    timeout: int = 120,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None
) -> dict:
    client = get_client(api_key)

    parts = [types.Part.from_text(prompt)]
    if input_image:
        parts.append(types.Part.from_image(types.Image.from_file(input_image)))

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
    )
    # Add image_config if aspect_ratio or resolution specified
    # (check SDK for exact field names)

    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=config,
    )

    # Extract image from response.candidates[0].content.parts
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            image_bytes = part.inline_data.data
            if output_path.lower().endswith('.png'):
                image_bytes = convert_to_png(image_bytes)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            print(f"Image saved to: {output_path}")
            return {"success": True}

    raise RuntimeError("No image found in response")
```

Note: The exact SDK types and field names must be verified against the `google-genai` package. The implementer should check `from google.genai import types` and use the correct constructors.

**Step 2: Update SKILL.md**

In `skills/image/SKILL.md`:
- Remove all mentions of OpenRouter, FLUX Pro, FLUX Flex
- Remove `--provider` from examples
- Remove "Option 2: OpenRouter" from Configuration section
- Update the "Available Models" table to only show Gemini models
- Replace `OPENROUTER_API_KEY` references with just `GEMINI_API_KEY`
- Add `${CLAUDE_SKILL_DIR}` to script path references

**Step 3: Test the migration**

Run (requires GEMINI_API_KEY):
```bash
uv run python skills/image/scripts/generate_image.py "A simple red circle on white background" -o /tmp/test_sdk_migration.png
```
Expected: Image saved successfully, no OpenRouter code paths hit.

**Step 4: Commit**

```bash
git add skills/image/scripts/generate_image.py skills/image/SKILL.md
git commit -m "feat!: migrate image skill to google-genai SDK, drop OpenRouter"
```

---

### Task 4: Migrate diagram skill to SDK

**Files:**
- Modify: `skills/diagram/scripts/generate_diagram_ai.py` (major rewrite of NanoBananaGenerator class)
- Modify: `skills/diagram/scripts/generate_diagram.py` (simplify wrapper)
- Modify: `skills/diagram/SKILL.md` (update model refs)

**Step 1: Rewrite NanoBananaGenerator to use SDK**

Key changes to `generate_diagram_ai.py`:
- Remove `__init__` provider detection logic (lines 109-171) — replace with `self.client = get_client(api_key)`
- Update model IDs: `gemini-3-pro-image-preview` → `gemini-3.1-pro-image-preview`, `gemini-3-pro-preview` → `gemini-3.1-pro-preview`
- Delete `_make_google_request()` (lines 184-228), `_make_request()` (lines 265-315) — replace with SDK calls
- Delete `_extract_image_from_google_response()` (lines 230-251), `_extract_image_from_response()` (lines 317-372), `_extract_text_from_google_response()` (lines 253-263) — SDK handles extraction
- Delete `_generate_image_openrouter()` (lines 440-473), `_review_image_openrouter()` (lines 489-521)
- Simplify `generate_image()` to single SDK path
- Simplify `review_image()` to single SDK path
- Remove `--provider` from argparse (line 829-831)
- Remove OpenRouter env var references from epilog

The `generate_image` method becomes:
```python
def generate_image(self, prompt: str, input_image: Optional[str] = None) -> Optional[bytes]:
    parts = [types.Part.from_text(prompt)]
    if input_image:
        parts.append(types.Part.from_image(types.Image.from_file(input_image)))

    config = types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
    # Add resolution via image_config if self.resolution is set

    try:
        response = self.client.models.generate_content(
            model=self.image_model, contents=parts, config=config
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                return part.inline_data.data
        return None
    except Exception as e:
        self._last_error = str(e)
        return None
```

The `review_image` method's API call becomes:
```python
response = self.client.models.generate_content(
    model=self.review_model,
    contents=[
        types.Part.from_text(review_prompt),
        types.Part.from_image(types.Image.from_file(image_path)),
    ],
)
return response.text
```

**Step 2: Simplify generate_diagram.py wrapper**

Remove `--provider` argument (lines 95-97), remove OpenRouter key detection (lines 111-116), simplify to just pass through to generate_diagram_ai.py.

**Step 3: Update diagram SKILL.md**

- Update model references from `gemini-3-pro-image-preview` to `gemini-3.1-pro-image-preview`
- Remove OpenRouter references
- Update review model reference to `gemini-3.1-pro-preview`

**Step 4: Test the migration**

Run (requires GEMINI_API_KEY):
```bash
uv run python skills/diagram/scripts/generate_diagram.py "Simple flowchart: start -> process -> end" -o /tmp/test_diagram_sdk.png --doc-type default
```
Expected: Diagram generated, quality reviewed, saved successfully.

**Step 5: Commit**

```bash
git add skills/diagram/scripts/generate_diagram_ai.py skills/diagram/scripts/generate_diagram.py skills/diagram/SKILL.md
git commit -m "feat!: migrate diagram skill to google-genai SDK, update to 3.1 models"
```

---

### Task 5: Create video generation script

**Files:**
- Create: `skills/video/scripts/__init__.py`
- Create: `skills/video/scripts/generate_video.py`

**Step 1: Create directory structure**

```bash
mkdir -p skills/video/scripts
touch skills/video/scripts/__init__.py
```

**Step 2: Write generate_video.py**

The full script implementing all video generation modes. Key components:

**Imports and setup:**
```python
#!/usr/bin/env python3
"""Generate videos using Veo 3.1 via Google Gemini API.

Supports text-to-video, image-to-video, frame interpolation,
video extension, and reference image guidance.

Usage:
    # Text-to-video
    python generate_video.py "Particles forming a logo" -o hero.mp4

    # Image-to-video (animate a still)
    python generate_video.py "Camera slowly zooms in" --input hero.png -o animated.mp4

    # Frame interpolation
    python generate_video.py "Smooth transition" --input slide1.png --last-frame slide2.png -o transition.mp4

    # With audio (opt-in, stripped by default)
    python generate_video.py "Narrator says: welcome" -o intro.mp4 --audio

    # Video extension
    python generate_video.py "Continue the scene" --extend previous.mp4 -o extended.mp4

    # 4K quality
    python generate_video.py "Drone shot" -o drone.mp4 -m veo-3.1-generate-preview --resolution 4k
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from common.client import get_client
from common.image_utils import get_mime_type
```

**Constraint validation:**
```python
def validate_constraints(args) -> None:
    """Validate Veo API constraints before making the call."""
    if args.resolution in ("1080p", "4k") and args.duration != 8:
        raise ValueError(f"{args.resolution} resolution requires --duration 8")
    if args.extend and args.resolution != "720p":
        raise ValueError("Video extension only supports 720p resolution")
    if args.reference and len(args.reference) > 3:
        raise ValueError("Maximum 3 reference images allowed")
    if args.extend and not args.extend.lower().endswith(".mp4"):
        raise ValueError("Extension requires an .mp4 video file")
    if args.last_frame and not args.input:
        raise ValueError("--last-frame requires --input (first frame)")
```

**Mode detection:**
```python
def detect_mode(args) -> str:
    if args.extend:
        return "extension"
    if args.input and args.last_frame:
        return "interpolation"
    if args.input:
        return "image-to-video"
    return "text-to-video"
```

**Audio stripping:**
```python
def strip_audio(input_path: str, output_path: str) -> bool:
    """Strip audio from video using ffmpeg. Returns True if successful."""
    if not shutil.which("ffmpeg"):
        print("Warning: ffmpeg not found. Video saved with audio.")
        print("Install ffmpeg to strip audio: brew install ffmpeg")
        shutil.move(input_path, output_path)
        return False
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-an", "-c:v", "copy", output_path],
            capture_output=True, timeout=30, check=True
        )
        os.unlink(input_path)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        shutil.move(input_path, output_path)
        return False
```

**Core generation:**
```python
from google.genai import types

def generate_video(
    prompt: str,
    model: str = "veo-3.1-fast-generate-preview",
    output_path: str = "generated_video.mp4",
    api_key: Optional[str] = None,
    input_image: Optional[str] = None,
    last_frame: Optional[str] = None,
    extend_video: Optional[str] = None,
    reference_images: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    duration: int = 8,
    keep_audio: bool = False,
    timeout: int = 360,
) -> dict:
    client = get_client(api_key)

    config = types.GenerateVideosConfig(
        aspect_ratio=aspect_ratio,
        resolution=resolution,
        duration_seconds=str(duration),
        person_generation="allow_all",
    )

    # Build reference images list if provided
    if reference_images:
        refs = []
        for ref_path in reference_images:
            ref_img = types.Image.from_file(ref_path)
            refs.append(types.VideoGenerationReferenceImage(
                image=ref_img, reference_type="asset"
            ))
        config.reference_images = refs

    # Set up last frame for interpolation
    if last_frame:
        config.last_frame = types.Image.from_file(last_frame)

    # Build the generation call
    kwargs = dict(model=model, prompt=prompt, config=config)

    if input_image:
        kwargs["image"] = types.Image.from_file(input_image)
    if extend_video:
        # For extension, the video comes from a previous generation
        # The implementer needs to check how to pass a local .mp4 file
        # This may require uploading via client.files.upload() first
        pass

    # Start async generation
    print(f"Starting video generation ({model})...")
    operation = client.models.generate_videos(**kwargs)

    # Poll until done
    elapsed = 0
    while not operation.done:
        time.sleep(10)
        elapsed += 10
        print(f"  Generating... ({elapsed}s)")
        if elapsed > timeout:
            raise RuntimeError(f"Video generation timed out after {timeout}s")
        operation = client.operations.get(operation)

    # Download the video
    video = operation.response.generated_videos[0]

    # Save to temp path first (for audio stripping)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if keep_audio:
        client.files.download(file=video.video)
        video.video.save(output_path)
        print(f"Video saved to: {output_path} (with audio, {duration}s, {resolution})")
    else:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        client.files.download(file=video.video)
        video.video.save(tmp_path)
        stripped = strip_audio(tmp_path, output_path)
        label = "audio stripped" if stripped else "with audio"
        print(f"Video saved to: {output_path} ({label}, {duration}s, {resolution})")

    return {"success": True, "output": output_path}
```

**Argparse and main:**
```python
def main():
    parser = argparse.ArgumentParser(
        description="Generate videos using Veo 3.1 via Google Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes (auto-detected from flags):
  text-to-video      Default - just provide a prompt
  image-to-video     Use --input to animate an image
  interpolation      Use --input + --last-frame for transitions
  extension          Use --extend to extend a previous Veo video

Models:
  veo-3.1-fast-generate-preview     Fast, default ($0.15/s at 720p)
  veo-3.1-generate-preview          Standard quality ($0.40/s at 720p)

Resolution & Duration Constraints:
  720p  → 4, 6, or 8 seconds
  1080p → 8 seconds only
  4k    → 8 seconds only
  Extension → 720p only

Audio:
  Audio is stripped by default (requires ffmpeg).
  Use --audio to keep the generated audio track.

Environment:
  GEMINI_API_KEY    Google Gemini API key (paid tier required)
        """
    )

    parser.add_argument("prompt", help="Text description of the video")
    parser.add_argument("-o", "--output", default="generated_video.mp4", help="Output file path")
    parser.add_argument("-m", "--model", default="veo-3.1-fast-generate-preview",
                       help="Model ID (default: veo-3.1-fast-generate-preview)")
    parser.add_argument("-i", "--input", help="Input image (image-to-video mode)")
    parser.add_argument("--last-frame", help="Last frame image (interpolation mode)")
    parser.add_argument("--extend", help="Video to extend (extension mode)")
    parser.add_argument("--reference", action="append", help="Reference image (max 3, repeatable)")
    parser.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16"],
                       help="Video aspect ratio (default: 16:9)")
    parser.add_argument("--resolution", default="720p", choices=["720p", "1080p", "4k"],
                       help="Video resolution (default: 720p)")
    parser.add_argument("--duration", type=int, default=8, choices=[4, 6, 8],
                       help="Video duration in seconds (default: 8)")
    parser.add_argument("--audio", action="store_true", help="Keep audio track (stripped by default)")
    parser.add_argument("--api-key", help="API key (or set GEMINI_API_KEY)")
    parser.add_argument("--timeout", type=int, default=360, help="Max generation time in seconds")

    args = parser.parse_args()

    try:
        validate_constraints(args)
        mode = detect_mode(args)

        print(f"\n{'='*50}")
        print(f"Nano Banana - Video Generation")
        print(f"{'='*50}")
        print(f"Mode: {mode}")
        print(f"Prompt: {args.prompt}")
        print(f"Model: {args.model}")
        print(f"Resolution: {args.resolution}")
        print(f"Duration: {args.duration}s")
        print(f"Aspect Ratio: {args.aspect_ratio}")
        print(f"Audio: {'keep' if args.audio else 'strip'}")
        print(f"Output: {args.output}")
        print(f"{'='*50}\n")

        generate_video(
            prompt=args.prompt,
            model=args.model,
            output_path=args.output,
            api_key=args.api_key,
            input_image=args.input,
            last_frame=args.last_frame,
            extend_video=args.extend,
            reference_images=args.reference,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            duration=args.duration,
            keep_audio=args.audio,
            timeout=args.timeout,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Important implementation notes for the developer:**
- The exact `google-genai` types API must be verified by checking `from google.genai import types` and inspecting available constructors. The code above uses the patterns from the official docs but field names may differ slightly in the Python SDK.
- Video extension may require uploading the video via `client.files.upload()` first — check the SDK.
- `person_generation` parameter varies by mode — see design doc constraints table.

**Step 3: Test argument parsing**

Run: `uv run python skills/video/scripts/generate_video.py --help`
Expected: Help text with all flags displayed correctly.

Run: `uv run python skills/video/scripts/generate_video.py "test" --resolution 4k --duration 4 -o /tmp/test.mp4`
Expected: Error "4k resolution requires --duration 8"

**Step 4: Commit**

```bash
git add skills/video/scripts/__init__.py skills/video/scripts/generate_video.py
git commit -m "feat: add video generation script with Veo 3.1 support"
```

---

### Task 6: Create video SKILL.md

**Files:**
- Create: `skills/video/SKILL.md`

**Step 1: Write the skill documentation**

Create `skills/video/SKILL.md` following Skill 2.0 spec:

```yaml
---
name: video
description: "Generate videos using Veo 3.1 via Google Gemini API. Supports text-to-video, image-to-video animation, frame interpolation between two images, video extension, and reference image guidance. Use when the user needs animated content, video assets, motion graphics, slide transitions, hero animations, or wants to animate an existing image or diagram. Pairs with the image and diagram skills for an image-to-video pipeline."
argument-hint: "[description or instruction]"
allowed-tools: [Read, Write, Edit, Bash]
disable-model-invocation: true
---
```

Body should include:
- Overview with key features
- When to use (vs image or diagram skills)
- Quick start examples for each mode (text-to-video, image-to-video, interpolation, extension)
- Available models table (Veo 3.1 Fast default, Veo 3.1 Standard for quality)
- Resolution/duration/pricing table
- Audio handling explanation (opt-in with --audio, ffmpeg required to strip)
- Image-to-video pipeline examples showing chaining with image/diagram skills
- Configuration (GEMINI_API_KEY, paid tier required)
- Troubleshooting section
- Use `${CLAUDE_SKILL_DIR}` for all script path references

Keep under 500 lines. Follow patterns from the existing `skills/image/SKILL.md` for consistency.

**Step 2: Commit**

```bash
git add skills/video/SKILL.md
git commit -m "feat: add video skill documentation (Skill 2.0)"
```

---

### Task 7: Update plugin manifest and hooks

**Files:**
- Modify: `.claude-plugin/plugin.json:24-28`
- Modify: `hooks/validate-output.py:20,23-65`
- Modify: `commands/setup.md`

**Step 1: Update plugin.json**

Add video skill to skills array:
```json
"skills": [
    "./skills/diagram",
    "./skills/image",
    "./skills/kroki",
    "./skills/video"
]
```

Add keywords: `"video-generation"`, `"veo"`. Remove `"openrouter"`.

Update description to mention video generation.

**Step 2: Update validate-output.py**

Add `"generate_video.py"` to `GENERATION_PATTERNS` at line 20:
```python
GENERATION_PATTERNS: List[str] = ["generate_image.py", "generate_diagram", "generate_video.py"]
```

Update error patterns (lines 23-65):
- Replace OpenRouter-specific messages with Gemini-appropriate ones
- Add video-specific error patterns (timeout for long generation, paid tier required)
- Add `.mp4` file validation (check file exists, non-empty, valid MP4 header `\x00\x00\x00`)

Add MP4 magic bytes check near line 67:
```python
MP4_FTYP_MARKER = b"ftyp"  # MP4 files have "ftyp" at bytes 4-7
```

Update `validate_output_file()` to also check `.mp4` files.

**Step 3: Update commands/setup.md**

Remove OpenRouter setup instructions. Add note that video generation requires GEMINI_API_KEY on a paid tier. Keep the Gemini key setup section.

**Step 4: Commit**

```bash
git add .claude-plugin/plugin.json hooks/validate-output.py commands/setup.md
git commit -m "feat: register video skill in plugin manifest and extend validation hook"
```

---

### Task 8: Update documentation

**Files:**
- Modify: `CLAUDE.md`
- Modify: `ARCHITECTURE.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

**Step 1: Update CLAUDE.md**

- Add video skill to Quick Reference table and Skills table
- Add `generate_video.py` usage examples
- Update provider info (Google-only, paid tier for video)
- Remove OpenRouter references
- Add "When to Use Which Skill" entry for video

**Step 2: Update ARCHITECTURE.md**

- Bump version to 3.0.0
- Add "Video Skill" section under Three-Skill System (now Four-Skill System)
- Document the SDK migration in Provider Architecture
- Remove OpenRouter section entirely
- Update model hierarchy table with new model IDs
- Add `skills/common/client.py` to Shared Utilities
- Add `skills/video/` to File Structure
- Add v3.0.0 to Version History

**Step 3: Update README.md**

- Add video skill to feature list and skills table
- Add video generation examples
- Update requirements (google-genai, ffmpeg optional)
- Remove OpenRouter references
- Update version badge to 3.0.0

**Step 4: Update CHANGELOG.md**

Add v3.0.0 entry:
```markdown
## [3.0.0] - 2026-03-12

### Breaking
- Migrated from urllib.request to google-genai SDK
- Removed OpenRouter support (--provider flag, OPENROUTER_API_KEY)
- FLUX models no longer available
- Diagram default model updated to gemini-3.1-pro-image-preview

### Added
- Video generation skill using Veo 3.1 (text-to-video, image-to-video, interpolation, extension, reference images)
- Shared google-genai client factory (skills/common/client.py)
- Audio control (--audio flag, stripped by default via ffmpeg)
- 4K video output support
- Portrait video support (9:16)

### Changed
- All skills now use google-genai SDK instead of raw urllib.request
- Diagram review model updated to gemini-3.1-pro-preview
- GEMINI_API_KEY required (was preferred, now mandatory)
- Plugin description updated to include video generation
```

**Step 5: Commit**

```bash
git add CLAUDE.md ARCHITECTURE.md README.md CHANGELOG.md
git commit -m "docs: update all documentation for v3.0.0"
```

---

### Task 9: Version bump to 3.0.0

**Files:**
- Modify: `.claude-plugin/plugin.json:3` (version)
- Modify: `pyproject.toml:3` (version)
- Modify: `README.md` (badge)
- Modify: `ARCHITECTURE.md:4` (version header)

**Step 1: Bump version in all files**

`.claude-plugin/plugin.json`: `"version": "3.0.0"`
`pyproject.toml`: `version = "3.0.0"`
`README.md`: Update badge from `version-2.0.0-blue` to `version-3.0.0-blue`
`ARCHITECTURE.md`: `**Version:** 3.0.0`

**Step 2: Commit and push**

```bash
git add .claude-plugin/plugin.json pyproject.toml README.md ARCHITECTURE.md
git commit -m "chore: bump version to 3.0.0"
git push
```

The push triggers the marketplace webhook which auto-updates `marketplace.json` in ~30 seconds.

**Step 3: Verify webhook**

Run: `gh run list --repo flight505/nano-banana --limit 1`
Expected: Recent workflow run for notify-marketplace.

---

## Dependency Graph

```
Task 1 (dependency)
  ├→ Task 2 (shared client)
  │   ├→ Task 3 (image migration)  ← independent
  │   ├→ Task 4 (diagram migration) ← independent
  │   └→ Task 5 (video script)      ← independent
  │       └→ Task 6 (video SKILL.md) ← can parallel with Task 5
  └→ Task 7 (manifest/hooks) ← after Tasks 3-6
      └→ Task 8 (docs) ← after Task 7
          └→ Task 9 (version bump) ← last
```

Tasks 3, 4, 5, and 6 can run in parallel after Tasks 1 and 2 are complete.
