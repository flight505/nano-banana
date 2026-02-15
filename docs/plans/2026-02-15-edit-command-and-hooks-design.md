# Nano Banana v1.1.0 — Edit Command & Hook Validation

**Date:** 2026-02-15
**Version:** 1.0.8 → 1.1.0 (minor bump — new feature)
**Approach:** Approach 2 — Edit command + PostToolUse validation

## Problem

Nano-banana works well for generation, but lacks:
1. An explicit edit workflow — users must manually construct `--input` flags
2. Output validation — silent failures produce broken files with no feedback
3. Error recovery guidance — API failures yield raw errors with no actionable advice
4. Skill hardening — skills can fire unintentionally, costing money

## Design

### 1. New `/nano-banana:edit` command

**File:** `commands/edit.md`

A new command invoked as `/nano-banana:edit path/to/image.png "Add a database component"`.

Behavior:
- Accepts `$ARGUMENTS` containing source image path + edit instructions
- Verifies the source file exists
- Determines if it's a diagram or general image from context
- For images: runs `generate_image.py` with `--input` flag
- For diagrams: runs `generate_diagram_ai.py` with new `--input` flag (sends existing diagram + edit prompt to Gemini 3 Pro Image, then runs quality review loop)
- Saves output as versioned file alongside original (e.g., `image_edit1.png`)

### 2. Skill hardening

**A. `disable-model-invocation: true`** added to `skills/image/SKILL.md` and `skills/diagram/SKILL.md` frontmatter. Prevents Claude from auto-triggering generation without explicit user request.

**B. SKILL.md prompt guidance refresh.** Sharpen prompt construction examples for Claude 4.6:
- Structured approach: subject, style, composition, technical details
- Edit workflow guidance: when to use `--input` vs. fresh generation
- Keep concise — improve what's there, don't bloat

**C. `--input` flag for `generate_diagram_ai.py`.** New parameter that sends the existing diagram image alongside the edit prompt to Gemini 3 Pro Image. The quality review loop stays the same — it starts from an edit rather than a blank canvas.

### 3. PostToolUse hook — output validation

**File:** `hooks/validate-output.py`
**Event:** `PostToolUse` on `Bash`
**Filter:** Only activates when command contains `generate_image.py` or `generate_diagram.py`

Validates:
1. Output file exists (parses `-o` flag from command)
2. Non-zero file size
3. Valid PNG header (first 8 bytes = `\x89PNG\r\n\x1a\n`)

On failure: returns `decision: "block"` with `additionalContext` explaining the issue.
On success: passes through silently.

Constraint: Fast, synchronous. No API calls. File-level validation only.

### 4. Error recovery (within PostToolUse)

**Same file:** `hooks/validate-output.py` handles both output validation AND error recovery in a single PostToolUse hook. When the Bash command fails, the `tool_result` contains the error output — the hook parses it for known patterns.

| Error Pattern | Guidance |
|---|---|
| `OPENROUTER_API_KEY not found` | Run `/nano-banana:setup` to configure API key |
| `API Error (401)` / `API Error (403)` | API key invalid or expired — check openrouter.ai/keys |
| `API Error (429)` | Rate limited — wait and retry, or check credits |
| `timed out` | Request timed out — try simpler prompt or retry |
| `Image file not found` | Source image path doesn't exist — verify path |
| Other | Generic failure with raw error for context |

No retries. Hook injects context via `systemMessage`; Claude decides next steps.

### 5. Plugin manifest & wiring

**`plugin.json` change:** Add `"hooks": "./hooks"` field.

**New files:**
```
hooks/
  hooks.json          — Hook event declarations (PostToolUse)
  validate-output.py  — Single validation + error recovery script
commands/
  edit.md             — New edit command
```

**Hook config (`hooks/hooks.json`) — plugin wrapper format:**
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

**Version bump:** 1.0.8 → 1.1.0 (triggers marketplace webhook automatically).

## Files Changed

| File | Action | Description |
|---|---|---|
| `commands/edit.md` | Create | New edit command |
| `hooks/hooks.json` | Create | Hook event declarations |
| `hooks/validate-output.py` | Create | Output validation + error recovery |
| `skills/image/SKILL.md` | Edit | Add disable-model-invocation, refresh prompts |
| `skills/diagram/SKILL.md` | Edit | Add disable-model-invocation, refresh prompts |
| `skills/diagram/scripts/generate_diagram_ai.py` | Edit | Add --input flag for editing |
| `.claude-plugin/plugin.json` | Edit | Add hooks field, bump version |

## Out of Scope

- MCP server configuration
- New models or batch generation
- Output versioning for image skill (can add later)
- Automatic retries in hooks
