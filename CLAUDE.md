# Nano Banana - Claude Code Plugin Instructions

This is a Claude Code plugin for AI-powered image and diagram generation.

## Quick Reference

| Command | Description |
|---------|-------------|
| `/nano-banana:setup` | Configure API keys and environment |

## Skills

| Skill | Description |
|-------|-------------|
| `diagram` | Generate technical diagrams with AI quality review |
| `image` | Generate and edit images using AI models |
| `mermaid` | Create text-based diagrams with Mermaid syntax |

## Usage

### Generate a Diagram

```bash
python skills/diagram/scripts/generate_diagram.py "description" -o output.png --doc-type TYPE
```

**Document Types:** `specification`, `architecture`, `proposal`, `journal`, `conference`, `thesis`, `grant`, `sprint`, `report`, `preprint`, `readme`, `poster`, `presentation`, `default`

### Generate an Image

```bash
python skills/image/scripts/generate_image.py "description" -o output.png
```

### Edit an Image

```bash
python skills/image/scripts/generate_image.py "edit instructions" --input source.png -o output.png
```

## Requirements

- `OPENROUTER_API_KEY` environment variable
- Python 3.8+ with `requests` library

## When to Use Which Skill

- **Technical diagrams** (architecture, flowcharts, ERD) → `diagram` skill
- **Creative images** (photos, art, illustrations) → `image` skill
- **Version-controlled diagrams** → `mermaid` skill

## Key Principles

1. **Smart iteration** - diagram skill only regenerates if quality below threshold
2. **Document-type aware** - different quality standards for different outputs
3. **AI review** - Gemini 3 Pro reviews each diagram generation
