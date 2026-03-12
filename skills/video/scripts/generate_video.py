#!/usr/bin/env python3
"""
Generate videos using Veo 3.1 — text-to-video, image-to-video, frame interpolation,
and video extension via the google-genai SDK.

Models:
- veo-3.1-fast-generate-preview (default — fast generation)
- veo-3.1-generate-preview (standard quality)

Usage:
    # Text-to-video
    python generate_video.py "A drone flyover of a coastal city at sunset" -o flyover.mp4

    # Image-to-video (animate a still image)
    python generate_video.py "Camera slowly zooms in" --input photo.png -o animated.mp4

    # Frame interpolation (first + last frame)
    python generate_video.py "Smooth transition" --input start.png --last-frame end.png -o interp.mp4

    # Video extension (continue an existing clip)
    python generate_video.py "The camera keeps panning right" --extend clip.mp4 -o extended.mp4

    # With reference images for style guidance
    python generate_video.py "A cat in this art style" -o styled.mp4 --reference style1.png --reference style2.png
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional

# Add skills/ to path for common imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from common.client import get_client  # noqa: E402
from google.genai import types  # noqa: E402

# ---------------------------------------------------------------------------
# Constraint validation
# ---------------------------------------------------------------------------

def validate_constraints(
    resolution: str,
    duration: int,
    extend: Optional[str],
    reference_images: List[str],
    input_image: Optional[str],
    last_frame: Optional[str],
) -> None:
    """Validate Veo 3.1 generation constraints. Exits on violation."""
    errors: List[str] = []

    # 1080p requires duration=8
    if resolution == "1080p" and duration != 8:
        errors.append(
            f"Resolution 1080p requires --duration 8 (got {duration}). "
            "Only 720p supports shorter durations."
        )

    # Extension requires 720p
    if extend and resolution != "720p":
        errors.append(
            f"Video extension requires --resolution 720p (got {resolution})."
        )

    # Max 3 reference images
    if len(reference_images) > 3:
        errors.append(
            f"Maximum 3 reference images allowed (got {len(reference_images)})."
        )

    # Extension needs an .mp4 input
    if extend:
        ext = Path(extend).suffix.lower()
        if ext != ".mp4":
            errors.append(
                f"Video extension requires an .mp4 file (got '{ext}')."
            )
        if not Path(extend).exists():
            errors.append(f"Extension video not found: {extend}")

    # last-frame requires input image
    if last_frame and not input_image:
        errors.append("--last-frame requires --input (first frame image).")

    # Validate input files exist
    if input_image and not Path(input_image).exists():
        errors.append(f"Input image not found: {input_image}")
    if last_frame and not Path(last_frame).exists():
        errors.append(f"Last frame image not found: {last_frame}")
    for ref in reference_images:
        if not Path(ref).exists():
            errors.append(f"Reference image not found: {ref}")

    if errors:
        print("\nConstraint validation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Audio stripping
# ---------------------------------------------------------------------------

def strip_audio(input_path: str, output_path: str) -> bool:
    """Strip audio from video using ffmpeg. Returns True if successful."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("Warning: ffmpeg not found — saving video with audio intact.")
        print("Install ffmpeg to automatically strip audio: brew install ffmpeg")
        return False

    try:
        subprocess.run(
            [ffmpeg, "-y", "-i", input_path, "-an", "-c:v", "copy", output_path],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Warning: ffmpeg audio strip failed: {e.stderr.decode()[:300]}")
        return False


# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------

def detect_mode(
    input_image: Optional[str],
    last_frame: Optional[str],
    extend: Optional[str],
) -> str:
    """Detect generation mode from CLI flags."""
    if extend:
        return "extension"
    if input_image and last_frame:
        return "interpolation"
    if input_image:
        return "image-to-video"
    return "text-to-video"


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------

def generate_video(
    prompt: str,
    output_path: str,
    model: str = "veo-3.1-fast-generate-preview",
    input_image: Optional[str] = None,
    last_frame: Optional[str] = None,
    extend: Optional[str] = None,
    reference_images: Optional[List[str]] = None,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    duration: int = 8,
    include_audio: bool = False,
    timeout: int = 360,
    api_key: Optional[str] = None,
) -> str:
    """Generate a video using Veo 3.1 via the google-genai SDK.

    Args:
        prompt: Text description or instruction for the video.
        output_path: Where to save the generated .mp4 file.
        model: Veo model ID.
        input_image: Path to input image (image-to-video / interpolation).
        last_frame: Path to last frame image (interpolation mode).
        extend: Path to .mp4 video to extend.
        reference_images: Up to 3 reference images for style guidance.
        aspect_ratio: '16:9' or '9:16'.
        resolution: '720p' or '1080p'.
        duration: Video duration in seconds (4, 6, or 8).
        include_audio: If True, keep generated audio. Default strips it.
        timeout: Max seconds to wait for generation.
        api_key: Override GEMINI_API_KEY.

    Returns:
        Path to the saved video file.

    Raises:
        ValueError: On API key issues.
        RuntimeError: On generation failure or timeout.
    """
    reference_images = reference_images or []
    mode = detect_mode(input_image, last_frame, extend)

    # Validate
    validate_constraints(resolution, duration, extend, reference_images, input_image, last_frame)

    # Print banner
    print(f"\n{'='*55}")
    print(f"Nano Banana - Video Generation ({mode})")
    print(f"{'='*55}")
    print(f"Prompt: {prompt}")
    print(f"Model: {model}")
    print(f"Mode: {mode}")
    print(f"Aspect Ratio: {aspect_ratio}")
    print(f"Resolution: {resolution}")
    print(f"Duration: {duration}s")
    print(f"Audio: {'included' if include_audio else 'stripped (use --audio to include)'}")
    if input_image:
        print(f"Input Image: {input_image}")
    if last_frame:
        print(f"Last Frame: {last_frame}")
    if extend:
        print(f"Extend Video: {extend}")
    if reference_images:
        print(f"Reference Images: {', '.join(reference_images)}")
    print(f"Output: {output_path}")
    print(f"Timeout: {timeout}s")
    print(f"{'='*55}\n")

    # Build client
    client = get_client(api_key)

    # Build config
    config_kwargs = {
        "number_of_videos": 1,
        "duration_seconds": duration,
        "enhance_prompt": True,
        "person_generation": "allow_adult",
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "generate_audio": include_audio,
    }

    # Frame interpolation: pass last_frame in config
    if last_frame:
        config_kwargs["last_frame"] = types.Image.from_file(last_frame)

    # Reference images via native SDK support
    if reference_images:
        config_kwargs["reference_images"] = [
            types.VideoGenerationReferenceImage(
                image=types.Image.from_file(ref_path),
                reference_type=types.VideoGenerationReferenceType.STYLE
                if len(reference_images) == 1
                else types.VideoGenerationReferenceType.ASSET,
            )
            for ref_path in reference_images
        ]

    config = types.GenerateVideosConfig(**config_kwargs)

    # Build generate_videos kwargs
    gen_kwargs = {
        "model": model,
        "prompt": prompt,
        "config": config,
    }

    # Mode-specific inputs
    if mode == "image-to-video" or mode == "interpolation":
        gen_kwargs["image"] = types.Image.from_file(input_image)
    elif mode == "extension":
        gen_kwargs["video"] = types.Video.from_file(extend)

    # Start generation
    print("Starting video generation...")
    t_start = time.time()
    operation = client.models.generate_videos(**gen_kwargs)

    # Poll until done or timeout
    poll_interval = 10
    while not operation.done:
        elapsed = time.time() - t_start
        if elapsed > timeout:
            raise RuntimeError(
                f"Video generation timed out after {timeout}s. "
                "Use --timeout to increase the limit."
            )
        remaining = timeout - elapsed
        wait = min(poll_interval, remaining)
        print(f"  Generating... ({elapsed:.0f}s elapsed, polling every {poll_interval}s)")
        time.sleep(wait)
        operation = client.operations.get(operation)

    elapsed = time.time() - t_start
    print(f"Generation complete ({elapsed:.1f}s)")

    # Extract and save video
    if not operation.response or not operation.response.generated_videos:
        raise RuntimeError("No video returned in the API response.")

    generated_video = operation.response.generated_videos[0]
    video_obj = generated_video.video

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    # Download and save the video
    client.files.download(file=video_obj)
    video_obj.save(output_path)
    print(f"Video saved to: {output_path}")

    # Backup audio stripping via ffmpeg (in case generate_audio=False wasn't honored)
    if not include_audio:
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            if strip_audio(output_path, tmp_path):
                Path(tmp_path).replace(output_path)
                print("Audio verified stripped from output.")
        finally:
            tmp_file = Path(tmp_path)
            if tmp_file.exists():
                tmp_file.unlink()

    file_size = Path(output_path).stat().st_size
    print(f"\nDone! Video: {output_path} ({file_size / 1024 / 1024:.1f} MB)")
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate videos using Veo 3.1 (google-genai SDK)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes (auto-detected from flags):
  text-to-video      Just a prompt (default)
  image-to-video     --input with an image file
  interpolation      --input + --last-frame
  extension          --extend with an .mp4 file

Models:
  veo-3.1-fast-generate-preview   Fast generation (default)
  veo-3.1-generate-preview        Standard quality

Constraints:
  - 1080p requires --duration 8
  - Video extension requires --resolution 720p
  - Max 3 --reference images

Environment:
  GEMINI_API_KEY    Google Gemini API key (required)
                    Get one at: https://aistudio.google.com/apikey

Examples:
  # Text-to-video
  python generate_video.py "A drone flyover of a coastal city" -o flyover.mp4

  # Image-to-video
  python generate_video.py "Slowly zoom in" --input photo.png -o animated.mp4

  # Frame interpolation
  python generate_video.py "Smooth morph" --input a.png --last-frame b.png -o morph.mp4

  # Extend a video
  python generate_video.py "Keep panning right" --extend clip.mp4 -o extended.mp4

  # 9:16 portrait, standard quality, 6 seconds
  python generate_video.py "Vertical reel" -o reel.mp4 --aspect-ratio 9:16 -m veo-3.1-generate-preview --duration 6

  # Keep generated audio
  python generate_video.py "A concert crowd cheering" -o concert.mp4 --audio
        """,
    )

    parser.add_argument(
        "prompt", type=str,
        help="Text description of the video to generate",
    )
    parser.add_argument(
        "-o", "--output", type=str, required=True,
        help="Output .mp4 file path",
    )
    parser.add_argument(
        "-m", "--model", type=str, default="veo-3.1-fast-generate-preview",
        help="Model ID (default: veo-3.1-fast-generate-preview)",
    )
    parser.add_argument(
        "-i", "--input", type=str, default=None,
        help="Input image for image-to-video or interpolation mode",
    )
    parser.add_argument(
        "--last-frame", type=str, default=None,
        help="Last frame image for frame interpolation (requires --input)",
    )
    parser.add_argument(
        "--extend", type=str, default=None,
        help="Video .mp4 file to extend",
    )
    parser.add_argument(
        "--reference", type=str, action="append", default=[],
        help="Reference image for style guidance (max 3, repeatable)",
    )
    parser.add_argument(
        "--aspect-ratio", type=str, default="16:9",
        choices=["16:9", "9:16"],
        help="Video aspect ratio (default: 16:9)",
    )
    parser.add_argument(
        "--resolution", type=str, default="720p",
        choices=["720p", "1080p"],
        help="Video resolution (default: 720p). Only 720p and 1080p supported.",
    )
    parser.add_argument(
        "--duration", type=int, default=8,
        choices=[4, 6, 8],
        help="Video duration in seconds (default: 8)",
    )
    parser.add_argument(
        "--audio", action="store_true", default=False,
        help="Keep generated audio (stripped by default)",
    )
    parser.add_argument(
        "--timeout", type=int, default=360,
        help="Max seconds to wait for generation (default: 360)",
    )
    parser.add_argument(
        "--api-key", type=str, default=None,
        help="Gemini API key (or set GEMINI_API_KEY env var)",
    )

    args = parser.parse_args()

    try:
        generate_video(
            prompt=args.prompt,
            output_path=args.output,
            model=args.model,
            input_image=args.input,
            last_frame=args.last_frame,
            extend=args.extend,
            reference_images=args.reference,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
            duration=args.duration,
            include_audio=args.audio,
            timeout=args.timeout,
            api_key=args.api_key,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
