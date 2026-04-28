#!/usr/bin/env python3
"""
Generate and edit images using Nano Banana 2 (fast) or Nano Banana Pro (quality).

Uses the google-genai SDK for Google Gemini API access.

Models:
- gemini-3.1-flash-image-preview (default - Nano Banana 2, fastest)
- gemini-3-pro-image-preview (Nano Banana Pro, highest quality)

Usage:
    # Generate a new image
    python generate_image.py "A beautiful sunset over mountains" -o sunset.png

    # Generate with specific aspect ratio and resolution
    python generate_image.py "A wide landscape" -o landscape.png --aspect-ratio 16:9 --resolution 2K

    # Edit an existing image
    python generate_image.py "Make the sky purple" --input photo.jpg -o edited.png

    # Edit with style references (multi-image input)
    python generate_image.py "Match the style of the references" \\
      --input scaffold.png --input-extra style.jpg --input-extra approved.jpg \\
      -o output.jpg -m gemini-3-pro-image-preview

    # Use Nano Banana Pro for highest quality
    python generate_image.py "Professional headshot" -m gemini-3-pro-image-preview -o headshot.png
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

# Add skills/ to path for common imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from common.client import get_client  # noqa: E402
from common.image_utils import convert_to_png, get_mime_type  # noqa: E402
from google.genai import types  # noqa: E402


def calculate_aspect_ratio(width: int, height: int) -> str:
    """Calculate aspect ratio string from width and height."""
    from math import gcd

    divisor = gcd(width, height)
    w_ratio = width // divisor
    h_ratio = height // divisor

    common_ratios = {
        (1, 1): "1:1",
        (16, 9): "16:9",
        (9, 16): "9:16",
        (4, 3): "4:3",
        (3, 4): "3:4",
        (3, 2): "3:2",
        (2, 3): "2:3",
        (2, 1): "2:1",
        (1, 2): "1:2",
    }

    if (w_ratio, h_ratio) in common_ratios:
        return common_ratios[(w_ratio, h_ratio)]
    return f"{w_ratio}:{h_ratio}"


def _save_image_bytes(image_bytes: bytes, output_path: str) -> None:
    """Save raw image bytes to file, converting to PNG if needed."""
    output_dir = Path(output_path).parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    if Path(output_path).suffix.lower() == ".png":
        image_bytes = convert_to_png(image_bytes)

    with open(output_path, "wb") as f:
        f.write(image_bytes)


def generate_image(
    prompt: str,
    model: str = "gemini-3.1-flash-image-preview",
    output_path: str = "generated_image.png",
    api_key: Optional[str] = None,
    input_image: Optional[str] = None,
    input_extras: Optional[list[str]] = None,
    timeout: int = 120,
    aspect_ratio: Optional[str] = None,
    resolution: Optional[str] = None,
) -> dict:
    """
    Generate or edit an image using the Google GenAI SDK.

    Args:
        prompt: Text description of the image to generate, or editing instructions
        model: Gemini model ID (default: gemini-3.1-flash-image-preview)
        output_path: Path to save the generated image
        api_key: API key (will auto-detect from environment if not provided)
        input_image: Path to an input image for editing (optional)
        input_extras: Additional input images for multi-image edit / style transfer
            (e.g. style references, approved-design references). Order matters —
            sent to the model after `input_image`.
        timeout: Request timeout in seconds (default: 120)
        aspect_ratio: Image aspect ratio (e.g. "16:9", "1:1", "4:3")
        resolution: Image resolution (512, 1K, 2K, 4K)

    Returns:
        dict: Summary with keys 'output_path', 'model', 'elapsed', and optionally 'text'

    Raises:
        ValueError: If no API key is found.
        FileNotFoundError: If any input image does not exist.
        RuntimeError: On API errors or missing image in response.
    """
    # Strip google/ prefix if present (legacy compat)
    if model.startswith("google/"):
        model = model.split("/", 1)[1]

    # Validate input image exists
    if input_image and not Path(input_image).exists():
        raise FileNotFoundError(f"Input image not found: {input_image}")

    # Validate extra inputs exist
    extras = input_extras or []
    for extra in extras:
        if not Path(extra).exists():
            raise FileNotFoundError(f"Extra input image not found: {extra}")

    is_editing = input_image is not None or bool(extras)
    total_inputs = (1 if input_image else 0) + len(extras)

    print(f"\n{'=' * 50}")
    print(f"Nano Banana - {'Editing' if is_editing else 'Generating'} Image")
    print(f"{'=' * 50}")

    if is_editing:
        if input_image:
            print(f"Input: {input_image}")
        for i, extra in enumerate(extras, start=1):
            print(f"Input-extra #{i}: {extra}")
        if total_inputs > 1:
            print(f"Total input images: {total_inputs}")
        print(f"Edit: {prompt}")
    else:
        print(f"Prompt: {prompt}")

    print(f"Model: {model}")
    print(f"Output: {output_path}")

    if aspect_ratio:
        print(f"Aspect Ratio: {aspect_ratio}")
    if resolution:
        print(f"Resolution: {resolution}")

    print(f"Timeout: {timeout}s")
    print(f"{'=' * 50}\n")

    # Build client
    client = get_client(api_key=api_key)

    # Build contents list — prompt first, then primary input, then extras in order
    contents: list = [prompt]
    if input_image:
        with open(input_image, "rb") as f:
            img_bytes = f.read()
        mime = get_mime_type(input_image)
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
    for extra in extras:
        with open(extra, "rb") as f:
            extra_bytes = f.read()
        extra_mime = get_mime_type(extra)
        contents.append(types.Part.from_bytes(data=extra_bytes, mime_type=extra_mime))

    # Build generation config
    config_kwargs: dict = {"response_modalities": ["TEXT", "IMAGE"]}
    if aspect_ratio or resolution:
        image_config_kwargs: dict = {}
        if aspect_ratio:
            image_config_kwargs["aspect_ratio"] = aspect_ratio
        if resolution:
            image_config_kwargs["image_size"] = resolution
        config_kwargs["image_config"] = types.ImageConfig(**image_config_kwargs)

    config = types.GenerateContentConfig(**config_kwargs)

    # Call the API
    t_start = time.time()
    try:
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )
    except Exception as e:
        elapsed = time.time() - t_start
        raise RuntimeError(f"API error: {e} (after {elapsed:.1f}s)") from e
    elapsed = time.time() - t_start

    # Extract image from response
    result: dict = {"output_path": output_path, "model": model, "elapsed": elapsed}
    text_parts: list[str] = []

    if response.parts:
        for part in response.parts:
            if part.text is not None:
                text_parts.append(part.text)
            elif part.inline_data is not None:
                _save_image_bytes(part.inline_data.data, output_path)
                print(f"Image saved to: {output_path} (elapsed: {elapsed:.1f}s)")
                if text_parts:
                    result["text"] = "\n".join(text_parts)
                return result

    extra = f"\nResponse text: {' '.join(text_parts)[:500]}..." if text_parts else ""
    raise RuntimeError(f"No image found in response (elapsed: {elapsed:.1f}s){extra}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate or edit images using Nano Banana 2 (Google GenAI SDK)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate an image
  python generate_image.py "A beautiful sunset over mountains" -o sunset.png

  # Generate with specific aspect ratio and resolution
  python generate_image.py "A wide landscape" -o landscape.png --aspect-ratio 16:9 --resolution 2K

  # Use Nano Banana Pro for highest quality
  python generate_image.py "Professional photo" -m gemini-3-pro-image-preview -o photo.png

  # Edit an existing image
  python generate_image.py "Make the sky purple" --input photo.jpg -o edited.png

  # Edit with style references (multi-image input — Pro model recommended)
  python generate_image.py "Match style of references" \\
    --input scaffold.png --input-extra style.jpg --input-extra approved.jpg \\
    -o output.jpg -m gemini-3-pro-image-preview

Models (Nano Banana family):
  - gemini-3.1-flash-image-preview (default, Nano Banana 2 -- fastest, general use)
  - gemini-3-pro-image-preview (Nano Banana Pro -- best quality, professional assets)

Aspect Ratios:
  1:1, 1:4, 1:8, 2:3, 3:2, 3:4, 4:1, 4:3, 4:5, 5:4, 8:1, 9:16, 16:9, 21:9

Resolutions:
  512, 1K, 2K, 4K

Environment:
  GEMINI_API_KEY        Google Gemini API key (free tier available)
        """,
    )

    parser.add_argument(
        "prompt", type=str, help="Text description of the image, or editing instructions"
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default="gemini-3.1-flash-image-preview",
        help="Model ID (default: gemini-3.1-flash-image-preview)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="generated_image.png",
        help="Output file path (default: generated_image.png)",
    )
    parser.add_argument(
        "--input", "-i", type=str, help="Input image path for editing (enables edit mode)"
    )
    parser.add_argument(
        "--input-extra",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Additional input image for multi-image edit / style transfer. "
            "Repeatable — pass once per extra image. Sent in order after --input. "
            "Recommended with -m gemini-3-pro-image-preview for best style preservation."
        ),
    )
    parser.add_argument(
        "--api-key", type=str, help="API key (or set GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "--aspect-ratio",
        type=str,
        choices=[
            "1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1",
            "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9",
        ],
        help="Image aspect ratio (e.g. 16:9, 1:1, 4:3)",
    )
    parser.add_argument(
        "--resolution",
        type=str,
        choices=["512", "1K", "2K", "4K"],
        help="Image resolution (512, 1K, 2K, 4K)",
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Request timeout in seconds (default: 120)"
    )

    args = parser.parse_args()

    try:
        generate_image(
            prompt=args.prompt,
            model=args.model,
            output_path=args.output,
            api_key=args.api_key,
            input_image=args.input,
            input_extras=args.input_extra,
            timeout=args.timeout,
            aspect_ratio=args.aspect_ratio,
            resolution=args.resolution,
        )
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
