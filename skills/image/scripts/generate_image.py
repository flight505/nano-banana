#!/usr/bin/env python3
"""
Generate and edit images using Nano Banana Pro via OpenRouter API.

Supports various image generation models:
- google/gemini-3-pro-image-preview (default - generation and editing)
- black-forest-labs/flux.2-pro (generation and editing)
- black-forest-labs/flux.2-flex (generation)

For image editing, provide an input image along with an editing prompt.

Usage:
    # Generate a new image
    python generate_image.py "A beautiful sunset over mountains" -o sunset.png

    # Edit an existing image
    python generate_image.py "Make the sky purple" --input photo.jpg -o edited.png

    # Use a specific model
    python generate_image.py "Abstract art" -m "black-forest-labs/flux.2-pro" -o art.png
"""

import sys
import json
import base64
import argparse
import os
from pathlib import Path
from typing import Optional


def check_env_file() -> Optional[str]:
    """Check if .env file exists and contains OPENROUTER_API_KEY."""
    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        env_file = parent / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENROUTER_API_KEY='):
                        api_key = line.split('=', 1)[1].strip().strip('"').strip("'")
                        if api_key:
                            return api_key
    return None


def load_image_as_base64(image_path: str) -> str:
    """Load an image file and return it as a base64 data URL."""
    path = Path(image_path)
    if not path.exists():
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)

    ext = path.suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    mime_type = mime_types.get(ext, 'image/png')

    with open(path, 'rb') as f:
        image_data = f.read()

    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:{mime_type};base64,{base64_data}"


def save_base64_image(base64_data: str, output_path: str) -> None:
    """Save base64 encoded image to file."""
    if ',' in base64_data:
        base64_data = base64_data.split(',', 1)[1]

    # Create output directory if needed
    output_dir = Path(output_path).parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    image_data = base64.b64decode(base64_data)
    with open(output_path, 'wb') as f:
        f.write(image_data)


def generate_image(
    prompt: str,
    model: str = "google/gemini-3-pro-image-preview",
    output_path: str = "generated_image.png",
    api_key: Optional[str] = None,
    input_image: Optional[str] = None
) -> dict:
    """
    Generate or edit an image using OpenRouter API.

    Args:
        prompt: Text description of the image to generate, or editing instructions
        model: OpenRouter model ID (default: google/gemini-3-pro-image-preview)
        output_path: Path to save the generated image
        api_key: OpenRouter API key (will check .env and environment if not provided)
        input_image: Path to an input image for editing (optional)

    Returns:
        dict: Response from OpenRouter API
    """
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found.")
        print("Install with: pip install requests")
        print("Or with uv: uv pip install requests")
        sys.exit(1)

    # Check for API key: param → env var → .env file
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        api_key = check_env_file()

    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found!")
        print("\nPlease set the environment variable:")
        print("  export OPENROUTER_API_KEY=your-api-key-here")
        print("\nOr create a .env file in your project directory with:")
        print("  OPENROUTER_API_KEY=your-api-key-here")
        print("\nGet your API key from: https://openrouter.ai/keys")
        sys.exit(1)

    is_editing = input_image is not None

    print(f"\n{'='*50}")
    print(f"🍌 Nano Banana - {'Editing' if is_editing else 'Generating'} Image")
    print(f"{'='*50}")

    if is_editing:
        print(f"📷 Input: {input_image}")
        print(f"✏️  Edit: {prompt}")

        image_data_url = load_image_as_base64(input_image)
        message_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}}
        ]
    else:
        print(f"📝 Prompt: {prompt}")
        message_content = prompt

    print(f"🤖 Model: {model}")
    print(f"💾 Output: {output_path}")
    print(f"{'='*50}\n")

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/flight505/nano-banana",
            "X-Title": "Nano Banana Image Generator"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": message_content}],
            "modalities": ["image", "text"]
        },
        timeout=120
    )

    if response.status_code != 200:
        print(f"❌ API Error ({response.status_code}): {response.text}")
        sys.exit(1)

    result = response.json()

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
                image_url = image["image_url"]["url"]
                save_base64_image(image_url, output_path)
                print(f"✅ Image saved to: {output_path}")
            elif "url" in image:
                save_base64_image(image["url"], output_path)
                print(f"✅ Image saved to: {output_path}")
            else:
                print(f"⚠️ Unexpected image format: {image}")
        else:
            print("⚠️ No image found in response")
            if message.get("content"):
                print(f"Response content: {message['content'][:500]}...")
    else:
        print("❌ No choices in response")
        print(f"Response: {json.dumps(result, indent=2)}")

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate or edit images using Nano Banana Pro via OpenRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with default model (Gemini 3 Pro Image Preview)
  python generate_image.py "A beautiful sunset over mountains" -o sunset.png

  # Use a specific model
  python generate_image.py "A cat in space" -m "black-forest-labs/flux.2-pro" -o cat.png

  # Edit an existing image
  python generate_image.py "Make the sky purple" --input photo.jpg -o edited.png

  # Edit with a specific model
  python generate_image.py "Add a hat to the person" --input portrait.png -m "black-forest-labs/flux.2-pro"

Popular image models:
  - google/gemini-3-pro-image-preview (default, high quality, generation + editing)
  - black-forest-labs/flux.2-pro (fast, high quality, generation + editing)
  - black-forest-labs/flux.2-flex (development version, generation only)

Environment:
  OPENROUTER_API_KEY    OpenRouter API key (required)
        """
    )

    parser.add_argument("prompt", type=str,
                       help="Text description of the image, or editing instructions")
    parser.add_argument("--model", "-m", type=str, default="google/gemini-3-pro-image-preview",
                       help="OpenRouter model ID (default: google/gemini-3-pro-image-preview)")
    parser.add_argument("--output", "-o", type=str, default="generated_image.png",
                       help="Output file path (default: generated_image.png)")
    parser.add_argument("--input", "-i", type=str,
                       help="Input image path for editing (enables edit mode)")
    parser.add_argument("--api-key", type=str,
                       help="OpenRouter API key (will check environment if not provided)")

    args = parser.parse_args()

    generate_image(
        prompt=args.prompt,
        model=args.model,
        output_path=args.output,
        api_key=args.api_key,
        input_image=args.input
    )


if __name__ == "__main__":
    main()
