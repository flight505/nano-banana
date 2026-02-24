#!/usr/bin/env python3
"""
Generate and edit images using Nano Banana Pro.

Supports Google Gemini API directly (preferred) and OpenRouter as fallback.

Models:
- gemini-3-pro-image-preview (default - generation and editing)
- black-forest-labs/flux.2-pro (OpenRouter only, generation and editing)
- black-forest-labs/flux.2-flex (OpenRouter only, generation only)

Usage:
    # Generate a new image (auto-detects best provider)
    python generate_image.py "A beautiful sunset over mountains" -o sunset.png

    # Force Google direct API
    python generate_image.py "A sunset" -o sunset.png --provider google

    # Edit an existing image
    python generate_image.py "Make the sky purple" --input photo.jpg -o edited.png

    # Use OpenRouter with a specific model
    python generate_image.py "Abstract art" -m "black-forest-labs/flux.2-pro" -o art.png --provider openrouter
"""

import sys
import json
import base64
import argparse
import os
import time
import urllib.request
import urllib.error
import socket
from pathlib import Path
from typing import Optional

# Add skills/ to path for common imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from common.image_utils import convert_to_png, get_mime_type, image_to_base64_url  # noqa: E402
from common.env import load_env_value  # noqa: E402


def save_base64_image(base64_data: str, output_path: str) -> None:
    """Save base64 encoded image to file."""
    if ',' in base64_data:
        base64_data = base64_data.split(',', 1)[1]

    output_dir = Path(output_path).parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    image_data = base64.b64decode(base64_data)
    if output_path.lower().endswith('.png'):
        image_data = convert_to_png(image_data)
    with open(output_path, 'wb') as f:
        f.write(image_data)


def calculate_aspect_ratio(width: int, height: int) -> str:
    """Calculate aspect ratio string from width and height."""
    from math import gcd
    divisor = gcd(width, height)
    w_ratio = width // divisor
    h_ratio = height // divisor

    common_ratios = {
        (1, 1): "1:1", (16, 9): "16:9", (9, 16): "9:16",
        (4, 3): "4:3", (3, 4): "3:4", (3, 2): "3:2",
        (2, 3): "2:3", (2, 1): "2:1", (1, 2): "1:2",
    }

    if (w_ratio, h_ratio) in common_ratios:
        return common_ratios[(w_ratio, h_ratio)]
    return f"{w_ratio}:{h_ratio}"


def _resolve_provider(api_key: Optional[str], provider: str) -> tuple:
    """Resolve which provider and API key to use.

    Returns (provider_name, api_key, model_name) tuple.

    Raises:
        ValueError: If the required API key is not found.
    """
    if provider == "google" or (provider == "auto" and not api_key):
        gemini_key = api_key if api_key and not api_key.startswith("sk-or-") else None
        if not gemini_key:
            gemini_key = os.getenv("GEMINI_API_KEY") or load_env_value("GEMINI_API_KEY")
        if gemini_key:
            return ("google", gemini_key, "gemini-3-pro-image-preview")
        if provider == "google":
            raise ValueError("GEMINI_API_KEY not found. Get one at: https://aistudio.google.com/apikey")

    if provider == "openrouter" or provider == "auto":
        or_key = api_key if api_key and api_key.startswith("sk-or-") else None
        if not or_key:
            or_key = os.getenv("OPENROUTER_API_KEY") or load_env_value("OPENROUTER_API_KEY")
        if or_key:
            return ("openrouter", or_key, "google/gemini-3-pro-image-preview")
        if provider == "openrouter":
            raise ValueError("OPENROUTER_API_KEY not found. Get one at: https://openrouter.ai/keys")

    raise ValueError(
        "No API key found!\n\n"
        "Set one of:\n"
        "  export GEMINI_API_KEY=your-key    (preferred, free tier)\n"
        "  export OPENROUTER_API_KEY=your-key\n\n"
        "Get a Gemini key at: https://aistudio.google.com/apikey"
    )


def _generate_via_google(
    prompt: str, api_key: str, model: str, output_path: str,
    input_image: Optional[str], timeout: int
) -> dict:
    """Generate image using Google Gemini API directly.

    Raises:
        RuntimeError: On API errors, timeouts, or missing image in response.
    """
    base_url = "https://generativelanguage.googleapis.com/v1beta"
    url = f"{base_url}/models/{model}:generateContent?key={api_key}"

    parts = [{"text": prompt}]
    if input_image:
        with open(input_image, "rb") as f:
            img_bytes = f.read()
        mime = get_mime_type(input_image)
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(img_bytes).decode()}})

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    t_start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            result = json.loads(response_body)
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t_start
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = str(e)
        raise RuntimeError(f"API Error ({e.code}): {error_body} (after {elapsed:.1f}s)")
    except urllib.error.URLError as e:
        elapsed = time.time() - t_start
        if isinstance(e.reason, socket.timeout):
            raise RuntimeError(f"Request timed out after {timeout}s (use --timeout to increase)")
        raise RuntimeError(f"Connection error: {e.reason} (after {elapsed:.1f}s)")
    except socket.timeout:
        raise RuntimeError(f"Request timed out after {timeout}s (use --timeout to increase)")
    elapsed = time.time() - t_start

    # Extract image from Google response
    candidates = result.get("candidates", [])
    if candidates:
        parts_out = candidates[0].get("content", {}).get("parts", [])
        for part in parts_out:
            if "inlineData" in part and part["inlineData"].get("mimeType", "").startswith("image/"):
                b64_data = part["inlineData"]["data"]
                image_bytes = base64.b64decode(b64_data)
                if Path(output_path).suffix.lower() == ".png":
                    image_bytes = convert_to_png(image_bytes)
                output_dir = Path(output_path).parent
                if output_dir and not output_dir.exists():
                    output_dir.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                print(f"Image saved to: {output_path} (elapsed: {elapsed:.1f}s)")
                return result

    text_parts = []
    if candidates:
        for part in candidates[0].get("content", {}).get("parts", []):
            if "text" in part:
                text_parts.append(part["text"])
    extra = f"\nResponse text: {' '.join(text_parts)[:500]}..." if text_parts else ""
    raise RuntimeError(f"No image found in Google response (elapsed: {elapsed:.1f}s){extra}")


def _generate_via_openrouter(
    prompt: str, api_key: str, model: str, output_path: str,
    input_image: Optional[str], width: Optional[int], height: Optional[int],
    timeout: int
) -> dict:
    """Generate image using OpenRouter API.

    Raises:
        RuntimeError: On API errors, timeouts, or missing image in response.
    """
    is_editing = input_image is not None

    if is_editing:
        image_data_url = image_to_base64_url(input_image)
        message_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}}
        ]
    else:
        message_content = prompt

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/flight505/nano-banana",
        "X-Title": "Nano Banana Image Generator"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message_content}],
        "modalities": ["image", "text"]
    }

    if width and height:
        aspect_ratio = calculate_aspect_ratio(width, height)
        image_config = {"aspect_ratio": aspect_ratio}
        max_dim = max(width, height)
        if max_dim <= 512:
            image_config["image_size"] = "1K"
        elif max_dim <= 1024:
            image_config["image_size"] = "2K"
        else:
            image_config["image_size"] = "4K"
        payload["image_config"] = image_config

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    t_start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")
            result = json.loads(response_body)
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t_start
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = str(e)
        raise RuntimeError(f"API Error ({e.code}): {error_body} (after {elapsed:.1f}s)")
    except urllib.error.URLError as e:
        elapsed = time.time() - t_start
        if isinstance(e.reason, socket.timeout):
            raise RuntimeError(f"Request timed out after {timeout}s (use --timeout to increase)")
        raise RuntimeError(f"Connection error: {e.reason} (after {elapsed:.1f}s)")
    except socket.timeout:
        raise RuntimeError(f"Request timed out after {timeout}s (use --timeout to increase)")
    elapsed = time.time() - t_start

    if result.get("choices"):
        message = result["choices"][0]["message"]
        images = []

        if message.get("images"):
            images = message["images"]
        elif message.get("content"):
            content = message["content"]
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image":
                        images.append(part)

        if images:
            image = images[0]
            if "image_url" in image:
                save_base64_image(image["image_url"]["url"], output_path)
                print(f"Image saved to: {output_path} (elapsed: {elapsed:.1f}s)")
            elif "url" in image:
                save_base64_image(image["url"], output_path)
                print(f"Image saved to: {output_path} (elapsed: {elapsed:.1f}s)")
            else:
                print(f"Unexpected image format: {image}")
        else:
            print(f"No image found in response (elapsed: {elapsed:.1f}s)")
            if message.get("content"):
                print(f"Response content: {message['content'][:500]}...")
    else:
        print(f"No choices in response (elapsed: {elapsed:.1f}s)")
        print(f"Response: {json.dumps(result, indent=2)}")

    return result


def generate_image(
    prompt: str,
    model: str = "google/gemini-3-pro-image-preview",
    output_path: str = "generated_image.png",
    api_key: Optional[str] = None,
    input_image: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    timeout: int = 120,
    provider: str = "auto"
) -> dict:
    """
    Generate or edit an image using Google Gemini API (preferred) or OpenRouter.

    Uses Python stdlib only - no external dependencies required.

    Args:
        prompt: Text description of the image to generate, or editing instructions
        model: Model ID (auto-mapped based on provider)
        output_path: Path to save the generated image
        api_key: API key (will auto-detect from environment if not provided)
        input_image: Path to an input image for editing (optional)
        width: Target image width in pixels (optional)
        height: Target image height in pixels (optional)
        timeout: Request timeout in seconds (default: 120)
        provider: API provider - "auto" (prefer Google), "google", or "openrouter"

    Returns:
        dict: Response from API

    Raises:
        ValueError: If no API key is found.
        FileNotFoundError: If the input image does not exist.
        RuntimeError: On API errors, timeouts, or missing image in response.
    """
    resolved_provider, resolved_key, default_model = _resolve_provider(api_key, provider)

    # Map model for Google provider
    if resolved_provider == "google":
        if model.startswith("google/"):
            model = model.split("/", 1)[1]
        if not model.startswith("gemini"):
            model = default_model

    # Validate input image exists
    if input_image and not Path(input_image).exists():
        raise FileNotFoundError(f"Input image not found: {input_image}")

    is_editing = input_image is not None

    print(f"\n{'='*50}")
    print(f"Nano Banana - {'Editing' if is_editing else 'Generating'} Image")
    print(f"{'='*50}")

    if is_editing:
        print(f"Input: {input_image}")
        print(f"Edit: {prompt}")
    else:
        print(f"Prompt: {prompt}")

    print(f"Provider: {resolved_provider}")
    print(f"Model: {model}")
    print(f"Output: {output_path}")

    if width and height:
        aspect_ratio = calculate_aspect_ratio(width, height)
        print(f"Dimensions: {width}x{height} (aspect ratio: {aspect_ratio})")

    print(f"Timeout: {timeout}s")
    print(f"{'='*50}\n")

    if resolved_provider == "google":
        return _generate_via_google(
            prompt=prompt, api_key=resolved_key, model=model,
            output_path=output_path, input_image=input_image, timeout=timeout
        )

    return _generate_via_openrouter(
        prompt=prompt, api_key=resolved_key, model=model,
        output_path=output_path, input_image=input_image,
        width=width, height=height, timeout=timeout
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate or edit images using Nano Banana Pro (Google Gemini or OpenRouter)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with auto-detected provider (prefers Google direct API)
  python generate_image.py "A beautiful sunset over mountains" -o sunset.png

  # Force Google direct API
  python generate_image.py "A sunset" -o sunset.png --provider google

  # Force OpenRouter
  python generate_image.py "A cat in space" -m "black-forest-labs/flux.2-pro" -o cat.png --provider openrouter

  # Edit an existing image
  python generate_image.py "Make the sky purple" --input photo.jpg -o edited.png

  # Generate with specific dimensions
  python generate_image.py "A simple icon" -o icon.png --width 256 --height 256

Providers:
  auto (default) - Prefers GEMINI_API_KEY (direct), falls back to OPENROUTER_API_KEY
  google         - Google Gemini API direct (free tier, reliable)
  openrouter     - OpenRouter (supports non-Google models like FLUX)

Models:
  - gemini-3-pro-image-preview (default, high quality, generation + editing)
  - black-forest-labs/flux.2-pro (OpenRouter only, fast, high quality)
  - black-forest-labs/flux.2-flex (OpenRouter only, development version)

Environment:
  GEMINI_API_KEY        Google Gemini API key (preferred, free tier)
  OPENROUTER_API_KEY    OpenRouter API key (fallback)
        """
    )

    parser.add_argument("prompt", type=str,
                       help="Text description of the image, or editing instructions")
    parser.add_argument("--model", "-m", type=str, default="google/gemini-3-pro-image-preview",
                       help="Model ID (default: google/gemini-3-pro-image-preview)")
    parser.add_argument("--output", "-o", type=str, default="generated_image.png",
                       help="Output file path (default: generated_image.png)")
    parser.add_argument("--input", "-i", type=str,
                       help="Input image path for editing (enables edit mode)")
    parser.add_argument("--provider", default="auto",
                       choices=["auto", "google", "openrouter"],
                       help="API provider: auto (prefer Google), google, or openrouter (default: auto)")
    parser.add_argument("--api-key", type=str,
                       help="API key (or set GEMINI_API_KEY / OPENROUTER_API_KEY)")
    parser.add_argument("--width", type=int,
                       help="Target image width in pixels (optional)")
    parser.add_argument("--height", type=int,
                       help="Target image height in pixels (optional)")
    parser.add_argument("--timeout", type=int, default=120,
                       help="Request timeout in seconds (default: 120)")

    args = parser.parse_args()

    if (args.width and not args.height) or (args.height and not args.width):
        parser.error("Both --width and --height must be specified together")

    if args.width and args.width < 1:
        parser.error("Width must be positive")

    if args.height and args.height < 1:
        parser.error("Height must be positive")

    try:
        generate_image(
            prompt=args.prompt,
            model=args.model,
            output_path=args.output,
            api_key=args.api_key,
            input_image=args.input,
            width=args.width,
            height=args.height,
            timeout=args.timeout,
            provider=args.provider
        )
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
