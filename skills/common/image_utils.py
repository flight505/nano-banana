"""Shared image utilities for Nano Banana skills."""

import base64
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# Standard MIME type mapping for image files
MIME_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def get_mime_type(file_path: str) -> str:
    """Get MIME type for an image file based on extension."""
    ext = Path(file_path).suffix.lower()
    return MIME_TYPES.get(ext, "image/png")


def image_to_base64_url(file_path: str) -> str:
    """Convert image file to base64 data URL.

    Raises:
        FileNotFoundError: If the image file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {file_path}")

    mime_type = get_mime_type(file_path)
    with open(path, "rb") as f:
        image_data = f.read()

    base64_data = base64.b64encode(image_data).decode("utf-8")
    return f"data:{mime_type};base64,{base64_data}"


def convert_to_png(data: bytes) -> bytes:
    """Convert image bytes to PNG format if needed.

    Tries PIL first, then macOS sips as fallback.
    Returns original bytes if conversion fails.
    """
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return data
    # Try PIL
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(data))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        pass
    # Try macOS sips
    tmp_in_path: Optional[str] = None
    tmp_out_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_in:
            tmp_in.write(data)
            tmp_in_path = tmp_in.name
        tmp_out_path = tmp_in_path.replace(".jpg", ".png")
        subprocess.run(
            ["sips", "-s", "format", "png", tmp_in_path, "--out", tmp_out_path],
            capture_output=True, timeout=10
        )
        with open(tmp_out_path, "rb") as f:
            png_data = f.read()
        if png_data[:8] == b'\x89PNG\r\n\x1a\n':
            return png_data
    except Exception:
        pass
    finally:
        for p in (tmp_in_path, tmp_out_path):
            if p:
                try:
                    os.unlink(p)
                except Exception:
                    pass
    return data  # fallback: return original
