"""Shared Google GenAI client factory for Nano Banana skills."""

import os
from typing import Optional

from google import genai

from .env import load_env_value


def get_client(api_key: Optional[str] = None) -> genai.Client:
    """Create a google-genai Client with automatic API key resolution.

    Resolution order:
        1. Explicit ``api_key`` argument
        2. ``GEMINI_API_KEY`` environment variable
        3. ``GEMINI_API_KEY`` from ``.env`` files (via ``load_env_value``)

    Returns:
        A configured ``genai.Client`` ready for API calls.

    Raises:
        ValueError: If no API key can be found.
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or load_env_value("GEMINI_API_KEY")

    if not key:
        raise ValueError(
            "GEMINI_API_KEY not found!\n\n"
            "Set it via:\n"
            "  export GEMINI_API_KEY=your-key\n\n"
            "Or create a .env file with:\n"
            "  GEMINI_API_KEY=your-key\n\n"
            "Get a free key at: https://aistudio.google.com/apikey\n\n"
            "Run /nano-banana:setup for guided configuration."
        )

    return genai.Client(api_key=key)
