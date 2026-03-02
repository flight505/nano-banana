<p align="center">
  <img src="assets/nano-banana-hero-voxel.png" alt="Nano Banana Hero - Epic Voxel Space Vista" width="800">
</p>

<p align="center">
  <a href="https://github.com/flight505/nano-banana"><img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/anthropics/claude-code"><img src="https://img.shields.io/badge/Claude%20Code-Plugin-purple.svg" alt="Claude Code Plugin"></a>
</p>

<p align="center">
  <strong>AI-powered image and diagram generation for Claude Code</strong><br>
  Using Google Gemini API (preferred) or OpenRouter with intelligent quality review
</p>

---

## Features

- **Zero Dependencies** - Uses Python stdlib only, works everywhere (no PEP 668 issues!)
- **Dual Provider** - Google Gemini API (free tier) with OpenRouter fallback
- **Smart Iteration** - Only regenerates when quality is below threshold (saves API calls)
- **Document-Type Aware** - 13 quality presets (journal, architecture, presentation, etc.)
- **AI Quality Review** - Gemini 3 Pro reviews each diagram generation
- **Multiple Skills** - Technical diagrams and general images
- **Image Editing** - Modify existing images with natural language

## Quick Start

### 1. Install the Plugin

```bash
git clone https://github.com/flight505/nano-banana.git
```

### 2. Configure API Key

**Option A: Google Gemini API (Recommended — free tier available)**

Get a key at [Google AI Studio](https://aistudio.google.com/apikey):

```bash
export GEMINI_API_KEY='your-gemini-key-here'
```

**Option B: OpenRouter (for FLUX and other non-Google models)**

Get a key at [OpenRouter](https://openrouter.ai/keys):

```bash
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
```

Or use a `.env` file in your project:

```bash
echo "GEMINI_API_KEY=your-key-here" > .env
```

### 3. Generate!

```bash
# Technical diagram with quality review
python3 skills/diagram/scripts/generate_diagram.py \
    "Microservices architecture with API gateway" \
    -o architecture.png \
    --doc-type architecture

# Creative image
python3 skills/image/scripts/generate_image.py \
    "A cozy coffee shop on a rainy day" \
    -o coffee_shop.png

# Edit an existing image
python3 skills/image/scripts/generate_image.py \
    "Add rain to the window" \
    --input coffee_shop.png -o rainy_coffee_shop.png
```

## Skills

### Diagram Skill

Generate publication-quality technical diagrams with AI quality review.

```bash
python3 skills/diagram/scripts/generate_diagram.py "User authentication flow" -o auth.png --doc-type architecture
```

**Document Types:**
| Type | Threshold | Use Case |
|------|-----------|----------|
| `specification` | 8.5/10 | Technical specs, PRDs |
| `architecture` | 8.0/10 | System architecture |
| `journal` | 8.5/10 | Academic papers |
| `presentation` | 6.5/10 | Slides (faster) |
| `readme` | 7.0/10 | Documentation |

[Full Diagram Documentation](skills/diagram/SKILL.md)

### Image Skill

Generate and edit images using various AI models.

```bash
# Generate
python3 skills/image/scripts/generate_image.py "Abstract art in blue and gold" -o art.png

# Edit existing image
python3 skills/image/scripts/generate_image.py "Make the sky purple" --input photo.jpg -o edited.png
```

**Available Models:**
- `gemini-3.1-flash-image-preview` (default — Nano Banana 2, fastest)
- `gemini-3-pro-image-preview` (Nano Banana Pro, highest quality)
- `black-forest-labs/flux.2-pro` (via OpenRouter)
- `black-forest-labs/flux.2-flex` (via OpenRouter)

**Aspect Ratio & Resolution:**
```bash
# Generate with specific aspect ratio and resolution
python3 skills/image/scripts/generate_image.py \
    "A wide cinematic landscape" -o landscape.png \
    --aspect-ratio 16:9 --resolution 2K
```

[Full Image Documentation](skills/image/SKILL.md)

### Kroki Skill

Render text-based diagrams (Mermaid, PlantUML, GraphViz, D2, and 23 more) to PNG/SVG.

```bash
# Render Mermaid to PNG
python3 skills/kroki/scripts/render_diagram.py -t mermaid -o flow.png \
    --source 'flowchart LR; A-->B-->C'

# Render PlantUML to SVG
python3 skills/kroki/scripts/render_diagram.py -t plantuml -i diagram.puml -o diagram.svg

# List all 27 supported types
python3 skills/kroki/scripts/render_diagram.py --list-types
```

[Full Kroki Documentation](skills/kroki/SKILL.md)

## When to Use Which Skill

| Need | Use |
|------|-----|
| Architecture diagrams (from description) | `diagram` |
| Flowcharts with boxes (from description) | `diagram` |
| ERD / data models (from description) | `diagram` |
| Photos / artistic images | `image` |
| Edit existing photos | `image` |
| Render Mermaid/PlantUML/DOT source | `kroki` |
| Render D2/C4/Excalidraw source | `kroki` |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Preferred | Google Gemini API key (free tier, direct, most reliable) |
| `OPENROUTER_API_KEY` | Alternative | OpenRouter API key (supports FLUX and non-Google models) |

**Auto-detection:** When both keys are set, Google Gemini is preferred. Use `--provider openrouter` to force OpenRouter.

### Setup Command

Run `/nano-banana:setup` in Claude Code for interactive configuration.

## Cost Estimates

| Operation | Estimated Cost |
|-----------|---------------|
| Simple diagram (1 iteration) | $0.05-0.15 |
| Complex diagram (2 iterations) | $0.10-0.30 |
| Image generation (Gemini) | Free tier / ~$0.02-0.10 |
| Image generation (FLUX) | $0.05-0.20 |

Smart iteration saves costs by stopping early when quality meets threshold.

## Plugin Structure

```
nano-banana/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest
├── commands/
│   ├── edit.md                  # /nano-banana:edit command
│   └── setup.md                 # /nano-banana:setup command
├── hooks/
│   ├── hooks.json               # PostToolUse hook declarations
│   └── validate-output.py       # Output validation + error recovery
├── skills/
│   ├── common/                  # Shared utilities
│   │   ├── __init__.py
│   │   ├── env.py               # Unified .env file loading (stdlib)
│   │   └── image_utils.py       # PNG conversion, MIME types, base64
│   ├── diagram/                 # Technical diagram generation
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── generate_diagram.py      # CLI wrapper
│   │       └── generate_diagram_ai.py   # AI generation + review logic
│   ├── image/                   # General image generation
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── generate_image.py        # Image generation/editing
│   └── kroki/                   # Text-based diagram rendering
│       ├── SKILL.md
│       └── scripts/
│           └── render_diagram.py        # Kroki.io rendering (27 types)
├── ARCHITECTURE.md              # Technical architecture documentation
├── CHANGELOG.md                 # Version history
├── CLAUDE.md                    # Developer instructions
├── pyproject.toml               # Python packaging (uv/pip)
└── README.md
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) for direct image generation API
- [OpenRouter](https://openrouter.ai) for multi-model API access
- [Claude Code](https://github.com/anthropics/claude-code) for the plugin platform
- Inspired by the [Claude Project Planner](https://github.com/flight505/claude-project-planner) plugin

## Issues & Contributions

- Report issues: [GitHub Issues](https://github.com/flight505/nano-banana/issues)
- Contributions welcome via Pull Requests

---

**Made with Nano Banana by [flight505](https://github.com/flight505)**
