"""Shared environment/config utilities for Nano Banana skills."""

from pathlib import Path
from typing import Optional


def load_env_value(key_name: str) -> Optional[str]:
    """Load a value from .env files in current or parent directories.

    Searches current directory and up to 5 parent levels for a .env file
    containing the given key. Does NOT require python-dotenv.

    Returns:
        The value if found, None otherwise.
    """
    current_dir = Path.cwd()
    search_dirs = [current_dir] + list(current_dir.parents)[:5]

    for directory in search_dirs:
        env_file = directory / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        if k.strip() == key_name:
                            return v.strip().strip('"').strip("'")
            except Exception:
                continue
    return None
