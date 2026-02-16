#!/usr/bin/env python3
"""PostToolUse validation hook for nano-banana generation output.

Reads JSON from stdin (Claude Code hook protocol). Validates output from
generate_image.py and generate_diagram scripts, providing error recovery
guidance and output file integrity checks.

Exit codes:
    0 - Success or non-matching command (silent pass-through)
    2 - Validation failure (JSON systemMessage on stderr)
"""

import json
import os
import shlex
import sys
from typing import List, Optional, Tuple

# Generation script patterns that trigger validation
GENERATION_PATTERNS: List[str] = ["generate_image.py", "generate_diagram"]

# Error patterns mapped to recovery guidance
ERROR_PATTERNS: List[Tuple[str, str]] = [
    (
        "OPENROUTER_API_KEY not found",
        "API key not configured. Run /nano-banana:setup to set up your OpenRouter API key.",
    ),
    (
        "API Error (401)",
        "API key is invalid or expired. Check your key at https://openrouter.ai/keys",
    ),
    (
        "API Error (403)",
        "API key lacks permissions. Check your key at https://openrouter.ai/keys",
    ),
    (
        "API Error (429)",
        "Rate limited by OpenRouter. Wait a moment and retry, or check your account credits at https://openrouter.ai/activity",
    ),
    (
        "timed out",
        "Request timed out. Try a simpler prompt, retry, or use --timeout to increase the limit.",
    ),
    (
        "Image file not found",
        "Source image path does not exist. Verify the file path and try again.",
    ),
    (
        "No image data in API response",
        "API returned no image. The model may have refused the prompt. Try rephrasing.",
    ),
    (
        "No choices in response",
        "API returned empty response. Check your OpenRouter account has credits.",
    ),
    (
        "Generation failed",
        "Image generation failed. Check the error output above for details.",
    ),
    # Anchored with trailing space to avoid false positives on success messages
    (
        "Error: ",
        "Image generation failed. Check the error output above for details.",
    ),
]

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def fail(message: str) -> None:
    """Exit with code 2 and a JSON systemMessage on stderr."""
    payload = json.dumps({"systemMessage": message})
    sys.stderr.write(payload + "\n")
    sys.exit(2)


def is_generation_command(command: str) -> bool:
    """Check if the Bash command invokes a nano-banana generation script."""
    return any(pattern in command for pattern in GENERATION_PATTERNS)


def check_error_patterns(tool_result: str) -> Optional[str]:
    """Match tool_result against known error patterns. Returns guidance or None."""
    for pattern, guidance in ERROR_PATTERNS:
        if pattern in tool_result:
            return guidance
    return None


def parse_output_path(command: str) -> Optional[str]:
    """Extract the output file path from -o or --output flag in the command."""
    try:
        tokens = shlex.split(command)
    except ValueError:
        # Fallback to simple split if shlex fails on malformed input
        tokens = command.split()

    for i, token in enumerate(tokens):
        if token in ("-o", "--output") and i + 1 < len(tokens):
            return tokens[i + 1]
        # Handle --output=path form
        if token.startswith("--output="):
            return token[len("--output="):]
    return None


def validate_output_file(file_path: str, cwd: str) -> Optional[str]:
    """Validate the output file exists, is non-empty, and has valid format.

    Returns an error message string on failure, or None on success.
    """
    # Resolve relative paths against cwd
    if not os.path.isabs(file_path):
        file_path = os.path.join(cwd, file_path)

    if not os.path.exists(file_path):
        return "Output file was not created: {}. Generation may have failed silently.".format(
            file_path
        )

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return "Output file is empty (0 bytes): {}. Generation produced no data.".format(
            file_path
        )

    # PNG header validation
    if file_path.lower().endswith(".png"):
        try:
            with open(file_path, "rb") as f:
                header = f.read(8)
            if header != PNG_MAGIC:
                return "Output file is not a valid PNG: {}. File may be corrupted.".format(
                    file_path
                )
        except IOError:
            return "Cannot read output file: {}. Check file permissions.".format(
                file_path
            )

    return None


def main() -> None:
    """Main hook entry point. Reads JSON from stdin, validates generation output."""
    try:
        raw = sys.stdin.read()
    except Exception:
        sys.exit(0)

    if not raw.strip():
        sys.exit(0)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    # Only process Bash tool invocations
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    # Extract command and check if it's a generation command
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not is_generation_command(command):
        sys.exit(0)

    # Check tool_result for known error patterns
    tool_result = str(data.get("tool_result", ""))
    guidance = check_error_patterns(tool_result)
    if guidance is not None:
        fail(guidance)

    # Validate output file if -o/--output was specified
    output_path = parse_output_path(command)
    if output_path is not None:
        cwd = data.get("cwd", os.getcwd())
        error = validate_output_file(output_path, cwd)
        if error is not None:
            fail(error)

    sys.exit(0)


if __name__ == "__main__":
    main()
