# Nano Banana v1.1.0 — Edit Command & Hook Validation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add explicit image/diagram editing, PostToolUse output validation, and skill hardening to nano-banana plugin.

**Architecture:** New `/nano-banana:edit` command wraps existing generation scripts with `--input` flag. A single PostToolUse hook validates all generation output (file existence, size, PNG validity) and provides error recovery guidance. Skills hardened with `disable-model-invocation: true`.

**Tech Stack:** Python 3.8+ stdlib, Claude Code plugin hooks (command type), Markdown commands with `$ARGUMENTS`.

**Design doc:** `docs/plans/2026-02-15-edit-command-and-hooks-design.md`

---

### Task 1: Create PostToolUse validation hook

**Files:**
- Create: `hooks/validate-output.py`
- Create: `hooks/hooks.json`

**Step 1: Create hooks directory and write validate-output.py**

```python
#!/usr/bin/env python3
"""PostToolUse hook: validates nano-banana generation output files.

Reads JSON from stdin (Claude Code hook protocol).
Only activates for Bash commands containing generate_image.py or generate_diagram.
Checks: file exists, non-zero size, valid PNG header.
On failure: exits 2 with recovery guidance on stderr (fed back to Claude).
On success: exits 0 silently.
"""

import json
import os
import re
import sys


def parse_output_path(command: str) -> str | None:
    """Extract -o/--output path from a generation command."""
    # Match -o path or --output path (with or without =)
    match = re.search(r'(?:-o|--output)[=\s]+["\']?([^\s"\']+)', command)
    return match.group(1) if match else None


def check_png_header(file_path: str) -> bool:
    """Check if file starts with valid PNG magic bytes."""
    PNG_MAGIC = b'\x89PNG\r\n\x1a\n'
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
        return header == PNG_MAGIC
    except (OSError, IOError):
        return False


def get_error_guidance(tool_result: str) -> str | None:
    """Match error patterns in tool_result and return targeted guidance."""
    patterns = [
        ("OPENROUTER_API_KEY not found", "API key not configured. Run /nano-banana:setup to set up your OpenRouter API key."),
        ("API Error (401)", "API key is invalid or expired. Check your key at https://openrouter.ai/keys"),
        ("API Error (403)", "API key lacks permissions. Check your key at https://openrouter.ai/keys"),
        ("API Error (429)", "Rate limited by OpenRouter. Wait a moment and retry, or check your account credits at https://openrouter.ai/activity"),
        ("timed out", "Request timed out after 120 seconds. Try a simpler prompt or retry."),
        ("Image file not found", "Source image path does not exist. Verify the file path and try again."),
        ("No image data in API response", "API returned no image. The model may have refused the prompt. Try rephrasing."),
        ("No choices in response", "API returned empty response. Check your OpenRouter account has credits."),
    ]
    for pattern, guidance in patterns:
        if pattern.lower() in tool_result.lower():
            return guidance
    return None


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = hook_input.get("tool_input", {}).get("command", "")
    if "generate_image.py" not in command and "generate_diagram" not in command:
        sys.exit(0)

    # Check tool_result for error patterns (handles failed Bash commands)
    tool_result = str(hook_input.get("tool_result", ""))

    # If the command itself failed, provide error recovery guidance
    error_guidance = get_error_guidance(tool_result)
    if error_guidance:
        print(json.dumps({"systemMessage": error_guidance}), file=sys.stderr)
        sys.exit(2)

    # Check for explicit failure markers in output
    if "Generation failed" in tool_result or "Error:" in tool_result:
        # Generic failure — check if we have a more specific pattern
        generic_msg = "Image generation failed. Check the error output above for details."
        print(json.dumps({"systemMessage": generic_msg}), file=sys.stderr)
        sys.exit(2)

    # Validate output file
    output_path = parse_output_path(command)
    if not output_path:
        sys.exit(0)  # Can't determine output path, skip validation

    # Resolve relative path against cwd
    cwd = hook_input.get("cwd", os.getcwd())
    if not os.path.isabs(output_path):
        output_path = os.path.join(cwd, output_path)

    if not os.path.exists(output_path):
        msg = f"Output file was not created at {output_path}. Generation may have failed silently. Check API key and account credits."
        print(json.dumps({"systemMessage": msg}), file=sys.stderr)
        sys.exit(2)

    file_size = os.path.getsize(output_path)
    if file_size == 0:
        msg = f"Output file {output_path} is empty (0 bytes). The API may have returned an empty response. Check your OpenRouter account credits."
        print(json.dumps({"systemMessage": msg}), file=sys.stderr)
        sys.exit(2)

    # Check PNG validity (only for .png files)
    if output_path.lower().endswith('.png') and not check_png_header(output_path):
        msg = f"Output file {output_path} is not a valid PNG image ({file_size} bytes). The file may be corrupted or contain error text instead of image data."
        print(json.dumps({"systemMessage": msg}), file=sys.stderr)
        sys.exit(2)

    # All checks passed — exit silently
    sys.exit(0)


if __name__ == "__main__":
    main()
```

**Step 2: Write hooks.json (plugin wrapper format)**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ${CLAUDE_PLUGIN_ROOT}/hooks/validate-output.py",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

**Step 3: Test hook with mock inputs**

Run these commands to verify the hook handles each case correctly:

```bash
# Test 1: Non-matching command (should exit 0, no output)
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"tool_result":"total 42","cwd":"/tmp"}' | python hooks/validate-output.py
echo "Exit: $?"
# Expected: Exit: 0, no output

# Test 2: Missing API key error (should exit 2 with guidance)
echo '{"tool_name":"Bash","tool_input":{"command":"python generate_image.py \"test\" -o test.png"},"tool_result":"OPENROUTER_API_KEY not found","cwd":"/tmp"}' | python hooks/validate-output.py 2>&1
echo "Exit: $?"
# Expected: Exit: 2, JSON with setup guidance

# Test 3: Timeout error (should exit 2 with guidance)
echo '{"tool_name":"Bash","tool_input":{"command":"python generate_image.py \"test\" -o test.png"},"tool_result":"Request timed out after 120 seconds","cwd":"/tmp"}' | python hooks/validate-output.py 2>&1
echo "Exit: $?"
# Expected: Exit: 2, JSON with timeout guidance

# Test 4: Missing output file (should exit 2)
echo '{"tool_name":"Bash","tool_input":{"command":"python generate_image.py \"test\" -o /tmp/nonexistent_nano_test.png"},"tool_result":"Image saved to: /tmp/nonexistent_nano_test.png","cwd":"/tmp"}' | python hooks/validate-output.py 2>&1
echo "Exit: $?"
# Expected: Exit: 2, file not created message

# Test 5: Non-Bash tool (should exit 0 immediately)
echo '{"tool_name":"Read","tool_input":{"file_path":"test.py"},"tool_result":"file contents"}' | python hooks/validate-output.py
echo "Exit: $?"
# Expected: Exit: 0, no output
```

**Step 4: Commit**

```bash
git add hooks/validate-output.py hooks/hooks.json
git commit -m "feat: add PostToolUse validation hook for generation output"
```

---

### Task 2: Add --input editing to diagram script

**Files:**
- Modify: `skills/diagram/scripts/generate_diagram_ai.py`

**Step 1: Add input_image parameter to generate_image method**

In `generate_diagram_ai.py`, modify the `generate_image` method (currently at line 306) to accept an optional `input_image` parameter:

```python
def generate_image(self, prompt: str, input_image: str = None) -> Optional[bytes]:
    """Generate or edit an image using Nano Banana Pro."""
    self._last_error = None

    if input_image:
        image_data_url = self._image_to_base64(input_image)
        message_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": image_data_url}}
        ]
    else:
        message_content = prompt

    messages = [{"role": "user", "content": message_content}]

    try:
        response = self._make_request(
            model=self.image_model,
            messages=messages,
            modalities=["image", "text"]
        )

        if "error" in response:
            error_msg = response["error"]
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))
            self._last_error = f"API Error: {error_msg}"
            print(f"✗ {self._last_error}")
            return None

        image_data = self._extract_image_from_response(response)
        if image_data:
            self._log(f"✓ Generated image ({len(image_data)} bytes)")
        else:
            self._last_error = "No image data in API response"
            self._log(f"✗ {self._last_error}")

        return image_data
    except RuntimeError as e:
        self._last_error = str(e)
        self._log(f"✗ Generation failed: {self._last_error}")
        return None
    except Exception as e:
        self._last_error = f"Unexpected error: {str(e)}"
        self._log(f"✗ Generation failed: {self._last_error}")
        return None
```

**Step 2: Add input_image parameter to generate_iterative method**

Modify `generate_iterative` (currently at line 448) to accept and use `input_image`:

```python
def generate_iterative(self, user_prompt: str, output_path: str,
                      iterations: int = 2,
                      doc_type: str = "default",
                      input_image: str = None) -> Dict[str, Any]:
```

In the method body, adjust the initial prompt and the generate call. Find the line `current_prompt = f"""{self.DIAGRAM_GUIDELINES}` (line ~474) and change it:

```python
        is_editing = input_image is not None

        if is_editing:
            current_prompt = f"""{self.DIAGRAM_GUIDELINES}

EDITING MODE: Modify the provided diagram based on these instructions.
Keep all existing elements unless the user explicitly asks to remove them.

USER EDIT REQUEST: {user_prompt}

Generate the updated diagram maintaining publication quality."""
        else:
            current_prompt = f"""{self.DIAGRAM_GUIDELINES}

USER REQUEST: {user_prompt}

Generate a publication-quality technical diagram that meets all the guidelines above."""
```

Then in the generation loop (line ~494), change the `generate_image` call:

```python
            image_data = self.generate_image(current_prompt, input_image=input_image if i == 1 else None)
```

Note: Only the first iteration uses the input image. Subsequent iterations refine based on critique alone (the model has already incorporated the source in iteration 1).

Also update the print header (line ~480):

```python
        print(f"\n{'='*60}")
        print(f"🍌 Nano Banana - {'Editing' if is_editing else 'Generating'} Diagram")
        print(f"{'='*60}")
        if is_editing:
            print(f"Source: {input_image}")
            print(f"Edit: {user_prompt}")
        else:
            print(f"Description: {user_prompt}")
```

**Step 3: Add --input to argparse in main()**

In the `main()` function (line ~576), add the `--input` argument after the existing arguments:

```python
    parser.add_argument("--input", "-i", type=str,
                       help="Input diagram image to edit (enables edit mode)")
```

And pass it to `generate_iterative` (line ~646):

```python
        # Validate input image if provided
        if args.input and not os.path.exists(args.input):
            print(f"Error: Input image not found: {args.input}")
            sys.exit(1)

        results = generator.generate_iterative(
            user_prompt=args.prompt,
            output_path=args.output,
            iterations=args.iterations,
            doc_type=args.doc_type,
            input_image=args.input
        )
```

**Step 4: Test argument parsing**

```bash
# Verify --input flag is recognized (will fail on API key, but confirms parsing works)
cd skills/diagram/scripts
python generate_diagram_ai.py "Test edit" -o /tmp/test.png --input /tmp/nonexistent.png 2>&1 | head -5
# Expected: "Error: Input image not found: /tmp/nonexistent.png"

python generate_diagram_ai.py --help | grep -A1 "\-\-input"
# Expected: Shows --input help text
```

**Step 5: Commit**

```bash
git add skills/diagram/scripts/generate_diagram_ai.py
git commit -m "feat: add --input flag for diagram editing"
```

---

### Task 3: Create /nano-banana:edit command

**Files:**
- Create: `commands/edit.md`

**Step 1: Write the edit command**

```markdown
---
description: Edit an existing image or diagram with AI
argument-hint: <source-image> <edit-instructions>
allowed-tools: [Read, Bash]
---

# Edit Existing Image or Diagram

The user wants to edit an existing image. Parse the arguments to extract:
1. **Source image path** — the first argument (a file path ending in .png, .jpg, .jpeg, .gif, .webp)
2. **Edit instructions** — everything after the source path

Arguments: $ARGUMENTS

## Steps

1. **Verify the source file exists** using the Read tool to confirm the path is valid.

2. **Determine the type** — check if the source was generated by nano-banana:
   - If the filename contains `diagram`, `_v1`, `_v2`, or there's a `*_review_log.json` alongside it → treat as a **diagram edit**
   - Otherwise → treat as an **image edit**

3. **Run the appropriate script:**

   For **image edits**:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/skills/image/scripts/generate_image.py "<edit-instructions>" --input <source-image> -o <output-path>
   ```

   For **diagram edits**:
   ```bash
   python ${CLAUDE_PLUGIN_ROOT}/skills/diagram/scripts/generate_diagram_ai.py "<edit-instructions>" --input <source-image> -o <output-path> --doc-type default
   ```

4. **Output naming** — save the edited version alongside the original:
   - If source is `architecture.png` → output as `architecture_edit1.png`
   - If `architecture_edit1.png` already exists → use `architecture_edit2.png`
   - Increment the edit number to avoid overwriting previous edits

5. **Report the result** — tell the user where the edited image was saved and what was changed.

## Important

- Always verify the source image exists before running any script
- Preserve the original file — never overwrite it
- If the user provides a diagram doc-type, pass it to the diagram script with `--doc-type`
- If arguments are missing or unclear, ask the user for the source path and edit instructions
```

**Step 2: Verify command renders correctly**

```bash
# Check file exists and has valid frontmatter
head -5 commands/edit.md
# Expected: --- / description: / argument-hint: / allowed-tools: / ---
```

**Step 3: Commit**

```bash
git add commands/edit.md
git commit -m "feat: add /nano-banana:edit command for iterative editing"
```

---

### Task 4: Harden skills

**Files:**
- Modify: `skills/image/SKILL.md` (frontmatter only)
- Modify: `skills/diagram/SKILL.md` (frontmatter only)

**Step 1: Add disable-model-invocation to image SKILL.md**

Change the frontmatter (lines 1-5) from:

```yaml
---
name: image
description: "Generate and edit images using AI models via OpenRouter. Supports Nano Banana Pro (Gemini 3 Pro Image), FLUX, and other image generation models."
allowed-tools: [Read, Write, Edit, Bash]
---
```

To:

```yaml
---
name: image
description: "Generate and edit images using AI models via OpenRouter. Supports Nano Banana Pro (Gemini 3 Pro Image), FLUX, and other image generation models."
allowed-tools: [Read, Write, Edit, Bash]
disable-model-invocation: true
---
```

**Step 2: Add disable-model-invocation to diagram SKILL.md**

Change the frontmatter (lines 1-5) from:

```yaml
---
name: diagram
description: "Generate publication-quality technical diagrams using Nano Banana Pro (Gemini 3 Pro Image) with AI-powered quality review. Smart iteration only regenerates when quality is below threshold."
allowed-tools: [Read, Write, Edit, Bash]
---
```

To:

```yaml
---
name: diagram
description: "Generate publication-quality technical diagrams using Nano Banana Pro (Gemini 3 Pro Image) with AI-powered quality review. Smart iteration only regenerates when quality is below threshold."
allowed-tools: [Read, Write, Edit, Bash]
disable-model-invocation: true
---
```

**Step 3: Add edit workflow guidance to image SKILL.md**

After the "Quick Start" section (line ~43), add:

```markdown
### Editing Existing Images

Use `/nano-banana:edit` to modify an existing image, or call the script directly:

```bash
# Edit via command (recommended)
/nano-banana:edit sunset.png "Add dramatic storm clouds and lightning"

# Edit via script directly
python skills/image/scripts/generate_image.py "Add dramatic storm clouds" --input sunset.png -o sunset_edit1.png
```

**When to edit vs. regenerate:**
- **Edit** when the base image is good but needs specific changes (add/remove elements, change colors, modify style)
- **Regenerate** when the image fundamentally doesn't match what you need
```

**Step 4: Add edit workflow guidance to diagram SKILL.md**

After the "Quick Start" section (line ~42), add:

```markdown
### Editing Existing Diagrams

Use `/nano-banana:edit` to modify an existing diagram, or call the script directly:

```bash
# Edit via command (recommended)
/nano-banana:edit architecture.png "Add a Redis cache layer between the API and database"

# Edit via script directly
python skills/diagram/scripts/generate_diagram_ai.py "Add Redis cache layer" --input architecture.png -o architecture_edit1.png --doc-type architecture
```

**When to edit vs. regenerate:**
- **Edit** when the diagram structure is correct but needs additions or modifications
- **Regenerate** when the layout or overall approach needs rethinking
```

**Step 5: Commit**

```bash
git add skills/image/SKILL.md skills/diagram/SKILL.md
git commit -m "feat: harden skills with disable-model-invocation and edit guidance"
```

---

### Task 5: Update plugin manifest

**Files:**
- Modify: `.claude-plugin/plugin.json`

**Step 1: Add hooks field and bump version**

Change `.claude-plugin/plugin.json` from:

```json
{
  "name": "nano-banana",
  "version": "1.0.8",
  "description": "AI-powered image and diagram generation for Claude Code - uses Nano Banana Pro (Gemini 3 Pro Image) with intelligent quality review and smart iteration.",
  "author": {
    "name": "Jesper Vang",
    "url": "https://github.com/flight505"
  },
  "license": "MIT",
  "repository": "https://github.com/flight505/nano-banana",
  "homepage": "https://github.com/flight505/nano-banana",
  "keywords": [
    "image-generation",
    "diagrams",
    "ai",
    "visualization",
    "openrouter",
    "mermaid",
    "technical-diagrams"
  ],
  "commands": "./commands",
  "skills": [
    "./skills/diagram",
    "./skills/image",
    "./skills/mermaid"
  ]
}
```

To:

```json
{
  "name": "nano-banana",
  "version": "1.1.0",
  "description": "AI-powered image and diagram generation for Claude Code - uses Nano Banana Pro (Gemini 3 Pro Image) with intelligent quality review and smart iteration.",
  "author": {
    "name": "Jesper Vang",
    "url": "https://github.com/flight505"
  },
  "license": "MIT",
  "repository": "https://github.com/flight505/nano-banana",
  "homepage": "https://github.com/flight505/nano-banana",
  "keywords": [
    "image-generation",
    "diagrams",
    "ai",
    "visualization",
    "openrouter",
    "mermaid",
    "technical-diagrams",
    "image-editing"
  ],
  "commands": "./commands",
  "skills": [
    "./skills/diagram",
    "./skills/image",
    "./skills/mermaid"
  ],
  "hooks": "./hooks"
}
```

Changes: version 1.0.8 → 1.1.0, added "image-editing" keyword, added "hooks" field.

**Step 2: Verify manifest is valid JSON**

```bash
python -c "import json; json.load(open('.claude-plugin/plugin.json')); print('Valid JSON')"
# Expected: Valid JSON
```

**Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add hooks to plugin manifest, bump version to 1.1.0"
```

---

### Task 6: Integration verification

**Files:** None (verification only)

**Step 1: Verify all new files exist**

```bash
ls -la hooks/validate-output.py hooks/hooks.json commands/edit.md
# Expected: All three files listed
```

**Step 2: Verify hooks.json is valid**

```bash
python -c "import json; data=json.load(open('hooks/hooks.json')); assert 'hooks' in data; assert 'PostToolUse' in data['hooks']; print('hooks.json valid')"
# Expected: hooks.json valid
```

**Step 3: Run hook tests from Task 1 Step 3**

Re-run all 5 hook test cases to confirm they still pass.

**Step 4: Verify diagram --input flag**

```bash
python skills/diagram/scripts/generate_diagram_ai.py --help | grep -A2 "input"
# Expected: --input flag documented
```

**Step 5: Verify plugin.json passes marketplace validator (if available)**

```bash
# From marketplace root (if accessible)
cd .. && python .claude/hooks/validators/plugin-manifest-validator.py < <(echo '{"tool_name":"Edit","tool_input":{"file_path":"nano-banana/.claude-plugin/plugin.json"}}') 2>&1; cd nano-banana
```

**Step 6: Final commit (if any fixes needed)**

```bash
git log --oneline -5
# Expected: 4 commits from tasks 1-5
```

---

## Summary of Changes

| Task | Commit Message | Files |
|------|---------------|-------|
| 1 | feat: add PostToolUse validation hook for generation output | hooks/validate-output.py, hooks/hooks.json |
| 2 | feat: add --input flag for diagram editing | skills/diagram/scripts/generate_diagram_ai.py |
| 3 | feat: add /nano-banana:edit command for iterative editing | commands/edit.md |
| 4 | feat: harden skills with disable-model-invocation and edit guidance | skills/image/SKILL.md, skills/diagram/SKILL.md |
| 5 | feat: add hooks to plugin manifest, bump version to 1.1.0 | .claude-plugin/plugin.json |
| 6 | (verification only, no commit) | — |

## Dependencies Between Tasks

- Task 2 (diagram --input) should be done before Task 3 (edit command) since the command references the flag
- Task 1 (hooks) is independent of Tasks 2-4
- Task 5 (manifest) should be last before verification
- Tasks 1, 2, and 4 can be done in parallel
