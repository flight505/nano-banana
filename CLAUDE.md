# Nano Banana - Claude Code Plugin Instructions

AI-powered image and diagram generation for Claude Code using Google Gemini API (preferred) or OpenRouter.

## Version Management & Marketplace Sync

**When committing version changes to `.claude-plugin/plugin.json`:**

1. **Bump version** following semantic versioning (MAJOR.MINOR.PATCH)
2. **Commit & push** to trigger webhook: `git commit -m "chore: bump version to X.Y.Z" && git push`
3. **Verify webhook** fired (5 sec): `gh run list --repo flight505/nano-banana --limit 1`
4. **Marketplace auto-syncs** within 30 seconds — no manual `marketplace.json` update needed

**Tip**: Use `../../scripts/bump-plugin-version.sh nano-banana X.Y.Z` to automate everything.

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `/nano-banana:setup` | Configure API keys and environment |
| `/nano-banana:edit` | Edit an existing image or diagram with AI |

## Skills

| Skill | Description |
|-------|-------------|
| `diagram` | Generate technical diagrams with AI quality review and smart iteration |
| `image` | Generate and edit images using AI models |
| `mermaid` | Create text-based diagrams with Mermaid syntax |

## Usage

### Generate a Diagram

```bash
python3 skills/diagram/scripts/generate_diagram.py "description" -o output.png --doc-type TYPE
```

**Document Types:** `specification`, `architecture`, `proposal`, `journal`, `conference`, `thesis`, `grant`, `sprint`, `report`, `preprint`, `readme`, `poster`, `presentation`, `default`

### Generate an Image

```bash
python3 skills/image/scripts/generate_image.py "description" -o output.png
```

### Edit an Image or Diagram

```bash
python3 skills/image/scripts/generate_image.py "edit instructions" --input source.png -o output.png
python3 skills/diagram/scripts/generate_diagram_ai.py "edit instructions" --input source.png -o output.png --doc-type architecture
```

### Force a Specific Provider

```bash
python3 skills/image/scripts/generate_image.py "description" -o output.png --provider google
python3 skills/diagram/scripts/generate_diagram.py "description" -o output.png --provider openrouter
```

## Requirements

- **GEMINI_API_KEY** (preferred) or **OPENROUTER_API_KEY** environment variable
- Python 3.8+ (stdlib only — no external dependencies)

## Provider Auto-Detection

1. If `GEMINI_API_KEY` is set → uses Google Gemini API directly (free tier, most reliable)
2. If only `OPENROUTER_API_KEY` is set → falls back to OpenRouter (supports FLUX and other non-Google models)
3. Use `--provider google` or `--provider openrouter` to override

## When to Use Which Skill

- **Technical diagrams** (architecture, flowcharts, ERD) → `diagram` skill
- **Creative images** (photos, art, illustrations) → `image` skill
- **Version-controlled diagrams** → `mermaid` skill

## Key Principles

1. **Zero dependencies** — uses Python stdlib only (`urllib.request`), no PEP 668 issues
2. **Smart iteration** — diagram skill only regenerates if quality below threshold
3. **Document-type aware** — 13 quality presets for different output contexts
4. **AI review** — Gemini 3 Pro reviews each diagram generation
5. **Shared utilities** — `skills/common/` provides reusable image and env helpers
