# CONTEXT_nano-banana.md

## Ground Truth Documentation

**Plugin:** Nano Banana
**Version:** 1.3.0
**Purpose:** AI-powered image and diagram generation for Claude Code
**Repository:** https://github.com/flight505/nano-banana
**Author:** flight505 (Jesper Vang)

---

## Architecture Overview

### Core Design Philosophy

Nano Banana is built on three foundational principles:

1. **Zero Dependencies** - Uses Python stdlib only (`urllib.request` instead of `requests`)
2. **Smart Iteration** - Only regenerates when quality is below threshold (cost optimization)
3. **Document-Type Awareness** - Different quality standards for different use cases
4. **Explicit Control** - Skills require explicit user invocation (`disable-model-invocation: true`)

### Three-Skill System

```
nano-banana/
├── skills/diagram/      → Technical diagrams with AI quality review
├── skills/image/        → General image generation and editing
└── skills/mermaid/      → Text-based diagrams (version control friendly)
```

**When to Use Which:**
- Technical diagrams (architecture, flowcharts, ERD) → `diagram`
- Creative images (photos, art, illustrations) → `image`
- Version-controlled diagrams (GitHub README) → `mermaid`

---

## Critical Implementation Details

### Zero-Dependency HTTP Client

**Location:** `/skills/common/http_client.py`

**Key Innovation (v1.0.3):**
- Replaced `requests` library with `urllib.request` (Python stdlib)
- Eliminated PEP 668 installation issues on modern Python environments
- No `pip install` required - just configure API key and run

**Design Pattern:**
```python
class OpenRouterClient:
    """HTTP client for OpenRouter API using Python stdlib only."""

    def chat_completion(model, messages, modalities=None, timeout=120):
        """Make API calls without external dependencies."""
        # Uses urllib.request internally
```

**Benefits:**
- Works on ALL Python 3.8+ environments
- No virtual environment conflicts
- No external package management required
- Faster plugin setup (no dependency installation step)

### Smart Iteration System

**Location:** `/skills/diagram/scripts/generate_diagram.py`

**Algorithm:**
1. Generate diagram using Nano Banana Pro (Gemini 3 Pro Image)
2. AI Quality Review evaluates 5 criteria (Gemini 3 Pro Vision)
3. If score < threshold: regenerate (max 2 iterations)
4. If score ≥ threshold: stop early (saves API calls)

**Quality Criteria (5 criteria, 0-2 points each, total 10):**
- Technical Accuracy (0-2)
- Clarity and Readability (0-2)
- Label Quality (0-2)
- Layout and Composition (0-2)
- Professional Appearance (0-2)

**Cost Optimization:**
- Early stopping prevents unnecessary regenerations
- Threshold-based iteration vs. fixed iteration count
- Estimated savings: 30-50% on simple diagrams

### Document-Type Thresholds

**13 Quality Presets:**

| Type | Threshold | Use Case | Rationale |
|------|-----------|----------|-----------|
| `specification` | 8.5/10 | Technical specs, PRDs | Highest standards for critical docs |
| `journal` | 8.5/10 | Academic papers | Publication quality |
| `architecture` | 8.0/10 | System architecture | Professional diagrams |
| `conference` | 8.0/10 | Conference papers | Academic presentations |
| `proposal` | 8.0/10 | Business proposals | Client-facing materials |
| `thesis` | 8.0/10 | PhD/Master thesis | Research documentation |
| `grant` | 8.0/10 | Grant applications | Funding proposals |
| `sprint` | 7.5/10 | Agile sprint docs | Internal team use |
| `report` | 7.5/10 | Technical reports | Standard documentation |
| `preprint` | 7.5/10 | arXiv, bioRxiv | Draft publications |
| `default` | 7.5/10 | General use | Balanced quality |
| `readme` | 7.0/10 | README files | GitHub documentation |
| `poster` | 7.0/10 | Conference posters | Visual emphasis |
| `presentation` | 6.5/10 | Slide decks | Faster generation for slides |

**Design Decision:**
- Higher thresholds for external/published documents
- Lower thresholds for internal/iterative work
- Presentation mode optimized for speed (not perfection)

---

## Hook System (v1.1.0)

### PostToolUse Output Validation

**Location:** `hooks/validate-output.py`
**Config:** `hooks/hooks.json`
**Event:** PostToolUse on Bash (5-second timeout)

**Activation:** Only fires for Bash commands containing `generate_image.py` or `generate_diagram`. All other commands pass through silently (exit 0).

**Two-phase validation:**

1. **Error pattern matching** — Checks `tool_result` for known error strings and provides targeted recovery guidance via `{"systemMessage": "..."}` on stderr (exit 2):
   - API key missing → "Run /nano-banana:setup"
   - HTTP 401/403 → "Check key at openrouter.ai/keys"
   - HTTP 429 → "Rate limited, wait and retry"
   - Timeout → "Try simpler prompt"
   - Missing source image → "Verify file path"

2. **Output file validation** — Parses `-o`/`--output` from the command, resolves against `cwd`, checks:
   - File exists
   - File size > 0
   - Valid PNG header (first 8 bytes = `\x89PNG\r\n\x1a\n`) for `.png` files

### Edit Workflow

**Command:** `/nano-banana:edit <source-image> <edit-instructions>`

**How it works:**
1. Parses source path and edit instructions from `$ARGUMENTS`
2. Auto-detects diagram vs. image (checks filename patterns, review log presence)
3. Routes to appropriate script with `--input` flag
4. Saves output with incremental naming (`_edit1`, `_edit2`, etc.)

**Diagram editing uses multimodal input:** The first iteration sends both the text prompt and the source image to Gemini 3 Pro Image. Subsequent iterations (if quality review triggers) refine based on critique alone.

---

## API Architecture

### OpenRouter Integration

**Primary Provider:** [OpenRouter](https://openrouter.ai)
**Required ENV:** `OPENROUTER_API_KEY`

**Models Used:**

1. **Nano Banana Pro** (Gemini 3 Pro Image)
   - Model ID: `google/gemini-3-pro-image-preview`
   - Purpose: Diagram generation with image output modality
   - Cost: ~$0.05-0.15 per diagram

2. **Gemini 3 Pro** (Vision/Text)
   - Model ID: `google/gemini-3-pro-preview`
   - Purpose: Quality review and critique
   - Cost: ~$0.01-0.05 per review

3. **FLUX Models** (Alternative)
   - `black-forest-labs/flux.2-pro` - High quality
   - `black-forest-labs/flux.2-flex` - Flexible/faster

**Why OpenRouter:**
- Single API for multiple AI models
- Unified billing and key management
- Model fallback capabilities
- No direct Google Cloud setup required

### Request Flow

```
User Description (or --input existing diagram + edit instructions)
    ↓
generate_diagram.py → generate_diagram_ai.py
    ↓
OpenRouterClient (stdlib HTTP)
    ↓
Gemini 3 Pro Image (generate or edit diagram)
    ↓
Base64 image response
    ↓
Gemini 3 Pro (quality review)
    ↓
Score >= threshold? → Save and exit
Score < threshold? → Regenerate (max 2 iterations)
```

---

## File Structure and Organization

### Root Structure

```
nano-banana/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (v1.1.0)
├── .github/
│   └── workflows/
│       └── notify-marketplace.yml  # Webhook to marketplace
├── assets/
│   └── nano-banana-hero-voxel.png  # Hero image
├── commands/
│   ├── edit.md                  # /nano-banana:edit command (v1.1.0)
│   └── setup.md                 # /nano-banana:setup command
├── hooks/
│   ├── hooks.json               # PostToolUse hook declarations (v1.1.0)
│   └── validate-output.py       # Output validation + error recovery (v1.1.0)
├── skills/
│   ├── common/
│   │   ├── __init__.py
│   │   └── http_client.py       # Zero-dependency HTTP client
│   ├── diagram/
│   │   ├── SKILL.md             # Diagram skill documentation
│   │   └── scripts/
│   │       ├── generate_diagram.py      # Main CLI
│   │       └── generate_diagram_ai.py   # AI generation logic
│   ├── image/
│   │   ├── SKILL.md             # Image skill documentation
│   │   └── scripts/
│   │       └── generate_image.py        # Image generation/editing CLI
│   └── mermaid/
│       └── SKILL.md             # Mermaid skill documentation
├── CHANGELOG.md                 # Version history
├── CLAUDE.md                    # Developer instructions
├── CONTEXT_nano-banana.md       # This file (ground truth)
├── LICENSE                      # MIT License
├── README.md                    # Public documentation
├── pyproject.toml               # Python packaging (uv/pip)
└── requirements.txt             # Empty (zero dependencies)
```

### Key Design Decisions

1. **skills/common/** - Shared utilities across all skills
   - `http_client.py` - OpenRouter API client (stdlib only)
   - Avoids code duplication between diagram/image skills

2. **scripts/** subdirectories - Direct CLI execution
   - `python3 skills/diagram/scripts/generate_diagram.py`
   - No package installation required

3. **SKILL.md** files - Skill-specific documentation
   - Stay in `/skills/` directory (not consolidated)
   - Reference documentation for each skill

4. **Zero dependencies** - `requirements.txt` is empty
   - Only `python-dotenv` in optional dependencies (for dev)
   - `pyproject.toml` declares no required dependencies

---

## Version History and Major Changes

### v1.1.0 (2026-02-16) - Current

**New Features:**
- `/nano-banana:edit` command for iterative editing of existing images and diagrams
- `--input` flag on both `generate_diagram.py` and `generate_diagram_ai.py` for diagram editing
- PostToolUse validation hook (`hooks/validate-output.py`) — validates generated files and provides error recovery guidance
- `disable-model-invocation: true` on image and diagram skills to prevent unintended generation

**Files Added:**
- `commands/edit.md` — Explicit edit command with `$ARGUMENTS`
- `hooks/hooks.json` — Hook event declarations (PostToolUse on Bash)
- `hooks/validate-output.py` — Output validation (file exists, non-zero, valid PNG header) + error pattern matching with recovery guidance

**Files Modified:**
- `skills/diagram/scripts/generate_diagram_ai.py` — `generate_image()` and `generate_iterative()` accept `input_image` parameter for multimodal editing
- `skills/diagram/scripts/generate_diagram.py` — Wrapper passes `--input` through to AI script
- `skills/image/SKILL.md` — Added `disable-model-invocation`, edit guidance, updated comparison table
- `skills/diagram/SKILL.md` — Added `disable-model-invocation`, edit guidance
- `.claude-plugin/plugin.json` — Added `hooks` field, `image-editing` keyword, version bump

### v1.0.8 (2026-01-24)
- Added width/height parameters with OpenRouter image_config support
- Dimension control via aspect ratio calculation

### v1.0.7 (2026-01-16)
- Updated plugin.json to match official Claude Code schema
- Version badge updates

### v1.0.5-1.0.6 (2026-01-13 to 2026-01-16)
- Webhook system testing and fixes
- Ground truth documentation (CONTEXT_nano-banana.md)

### v1.0.4 (2026-01-10)
- Documentation improvements
- Hero image and badge updates

### v1.0.3 (2025-01-08) - **Critical Architectural Change**

**🔥 Zero Dependencies Rewrite:**
- **Breaking Change:** Removed `requests` library dependency
- **Replacement:** Rewrote HTTP layer using `urllib.request` (Python stdlib)
- **Impact:** No more PEP 668 issues, works on all modern Python environments
- **Migration:** No code changes required - transparent replacement

**Files Changed:**
- `skills/common/http_client.py` - Complete rewrite
- `pyproject.toml` - Removed `requests` from dependencies
- `requirements.txt` - Now empty
- `commands/setup.md` - Removed installation step

**Rationale:**
- Modern Python environments (PEP 668) restrict `pip install` in system Python
- Users were experiencing dependency installation failures
- `urllib.request` is stdlib - always available, zero setup
- Slight API complexity increase, but massive UX improvement

### v1.0.2 (2025-01-07)
- Added hero logo and README styling

### v1.0.1 (2025-01-07)
- Fixed plugin schema (marketplace.json)
- Fixed skills format in plugin.json
- uv compatibility improvements

### v1.0.0 (2025-01-07) - Initial Release

**Origin:** Extracted from [Claude Project Planner](https://github.com/flight505/claude-project-planner)

**Initial Features:**
- Diagram skill with smart iteration
- Image skill with generation/editing
- Mermaid skill for text-based diagrams
- 13 document-type quality presets
- AI quality review system
- Setup command for configuration

**Key Improvements over Source:**
- Standalone plugin (no project planning dependencies)
- Cleaner branding (Nano Banana)
- Added `readme` document type (7.0 threshold)
- uv-compatible Python packaging
- Simplified directory structure

---

## Development Workflow

### Local Development

```bash
# Clone repository
git clone https://github.com/flight505/nano-banana.git
cd nano-banana

# Install dev dependencies (optional)
uv pip install -e ".[dev]"
# OR
pip install -e ".[dev]"

# Configure API key
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'

# Test diagram generation
python3 skills/diagram/scripts/generate_diagram.py \
    "Test architecture diagram" \
    -o test.png \
    --doc-type architecture \
    -v
```

### Plugin Installation

**User Method:**
```bash
# Install via Claude Code plugin system
claude plugin add https://github.com/flight505/nano-banana.git

# OR manual installation
cd ~/.claude/plugins
git clone https://github.com/flight505/nano-banana.git

# Configure via setup command
/nano-banana:setup
```

### Testing

```bash
# Run tests (when implemented)
pytest

# Lint code
ruff check .
ruff format .
```

### Version Bumping

```bash
# 1. Update version in plugin.json
cd .claude-plugin
jq '.version = "1.0.6"' plugin.json > tmp && mv tmp plugin.json

# 2. Update pyproject.toml
cd ..
# Edit version in pyproject.toml manually

# 3. Update CHANGELOG.md
# Add new version section

# 4. Commit and push (triggers webhook)
git add .
git commit -m "chore: bump version to 1.0.6"
git push origin main

# 5. Webhook auto-updates marketplace (~30 seconds)
```

---

## API Usage and Cost Structure

### Cost Estimates

**Diagram Generation (with smart iteration):**

| Scenario | Iterations | Cost |
|----------|-----------|------|
| Simple diagram (meets threshold first try) | 1 | $0.05-0.10 |
| Medium complexity (2 iterations) | 2 | $0.10-0.20 |
| Complex/high threshold (2 iterations) | 2 | $0.10-0.20 |

**Cost Breakdown:**
- Diagram generation: ~$0.03-0.08 per image
- Quality review: ~$0.01-0.02 per review
- Total per iteration: ~$0.05-0.10

**Smart Iteration Savings:**
- Without smart iteration (fixed 2 iterations): $0.10-0.20
- With smart iteration (early stopping): $0.05-0.10
- Average savings: 30-50%

**Image Generation:**
- Gemini 3 Pro Image: ~$0.02-0.10 per image
- FLUX Pro: ~$0.10-0.20 per image
- FLUX Flex: ~$0.05-0.10 per image

### Rate Limits

**OpenRouter Free Tier:**
- $5 credit on signup
- Rate limits vary by model
- No hard daily limits

**Recommendations:**
- Start with `presentation` doc type (lower threshold) for testing
- Use `specification` or `journal` only for final outputs
- Monitor costs via OpenRouter dashboard

### Error Handling

**Common Errors:**

1. **Missing API Key**
   - Error: `OPENROUTER_API_KEY environment variable is required`
   - Solution: Run `/nano-banana:setup` or export key

2. **Network Timeout**
   - Error: `TimeoutError: Request timed out`
   - Solution: Increase timeout or retry
   - Default timeout: 120 seconds

3. **HTTP 401 Unauthorized**
   - Error: `HTTP 401: Invalid API key`
   - Solution: Check API key format and validity

4. **HTTP 429 Rate Limited**
   - Error: `HTTP 429: Too many requests`
   - Solution: Wait and retry, or upgrade OpenRouter plan

---

## Integration with Marketplace

### Webhook System

**Notification Workflow:**
`.github/workflows/notify-marketplace.yml`

**Trigger Conditions:**
- Version change in `.claude-plugin/plugin.json`
- Push to `main` branch

**Flow:**
```
Version bump → Push to main
    ↓
notify-marketplace.yml (plugin repo)
    ↓
repository_dispatch event
    ↓
auto-update-plugins.yml (marketplace repo)
    ↓
Update marketplace.json + submodule pointer
    ↓
Users see new version (~30 seconds)
```

### Marketplace Entry

**Category:** `productivity` (or `development`)
**Keywords:** `image-generation`, `diagram`, `ai`, `visualization`, `gemini`

**marketplace.json Entry:**
```json
{
  "name": "nano-banana",
  "description": "AI-powered image and diagram generation using Nano Banana Pro with smart quality review",
  "version": "1.1.0",
  "author": {
    "name": "Jesper Vang",
    "url": "https://github.com/flight505"
  },
  "source": "./nano-banana",
  "category": "productivity",
  "keywords": ["image-generation", "diagram", "ai", "visualization", "image-editing"]
}
```

---

## Technical Constraints and Limitations

### Python Version Support

**Minimum:** Python 3.8
**Tested:** 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

**Why 3.8+:**
- Type hints (`Dict[str, Any]`, `Optional`, `List`)
- f-strings
- `urllib.request` modern API

### Platform Support

**Supported:**
- macOS (primary development platform)
- Linux (all distributions)
- Windows (with WSL or native Python)

**Requirements:**
- Internet connection (API calls)
- Filesystem write access (saving images)

### OpenRouter API Dependencies

**Critical:**
- Plugin is 100% dependent on OpenRouter availability
- No fallback to local models or alternative APIs
- Users must have valid OpenRouter API key

**Mitigation:**
- OpenRouter has 99.9% uptime SLA
- Supports multiple model providers (Google, Anthropic, etc.)
- Users can switch models without code changes

### Output Format Limitations

**Diagram Skill:**
- Output: PNG images (base64 decoded)
- Resolution: Determined by model (typically 1024x1024 to 2048x2048)
- No vector output (SVG) — tested and rejected (see Future Development)

**Image Skill:**
- Output: PNG images
- Editing: Requires input image as file path
- No batch generation support

**Mermaid Skill:**
- Output: Text/markdown (no rendering)
- Rendering: User's markdown viewer (GitHub, GitLab, Obsidian)

---

## Future Development Considerations

### Potential Enhancements

1. **Caching Layer**
   - Cache diagram descriptions → image mappings
   - Reduce duplicate API calls
   - Estimated savings: 10-20% for repeated requests

2. **Batch Generation**
   - Generate multiple diagrams in parallel
   - Useful for documentation sets

3. **Vector Output (SVG)** — ❌ TESTED, NOT VIABLE
   - Tested in Feb 2026 using Gemini 3 Pro (text model) to generate SVG code
   - Approach: prompt → text model (no image modality) → extract `<svg>` from response → save as `.svg`
   - **Results:** SVG output quality was significantly worse than PNG raster for both diagrams and icons
   - The text model produces structurally valid SVG but visually poor output — crude shapes, bad proportions, missing detail compared to the image model's raster output
   - Self-review scored SVG 10/10 (reviewing its own code) while the visual result was clearly inferior
   - **Conclusion:** Current text models cannot match image generation models for visual quality. SVG generation should only be revisited when image models can natively output vector formats.

4. **Local Model Support**
   - Optional local model fallback
   - Privacy-sensitive use cases

5. **Custom Quality Criteria**
   - User-defined review criteria
   - Domain-specific quality metrics

### Known Issues

1. **~~Timeout on Complex Diagrams~~** ✅ RESOLVED (v1.2.0)
   - `--timeout` CLI flag added to all generation scripts (default: 120s)
   - Applies per API request, not total process time
   - Diagram generation with 2 iterations can make up to 4 API calls (2 generation + 2 review)
   - Example: `--timeout 300` gives each API call 5 minutes to respond

2. **~~No Progress Indication~~** ✅ RESOLVED (v1.2.0)
   - Elapsed time logging added to all generation stages
   - Per-stage timing: generation, review, and total time displayed
   - Note: Spinners/progress bars are NOT viable inside Claude Code (Bash tool captures output, not streamed in real-time; ANSI escape codes produce garbage). Claude Code shows its own spinner during command execution.
   - Example output: `✓ Saved: diagram_v1.png (elapsed: 42.3s)`

---

## References and External Dependencies

### External Services

- **OpenRouter API** - https://openrouter.ai
- **Google Gemini** - Model provider (via OpenRouter)
- **Black Forest Labs FLUX** - Alternative image models

### Documentation

- **Claude Code Plugin Docs** - https://github.com/anthropics/claude-code/blob/main/docs/plugins.md
- **OpenRouter Docs** - https://openrouter.ai/docs
- **Gemini API Docs** - https://ai.google.dev/gemini-api/docs

### Related Projects

- **Claude Project Planner** - https://github.com/flight505/claude-project-planner (origin)
- **SDK Bridge** - https://github.com/flight505/sdk-bridge (marketplace companion)
- **Storybook Assistant** - https://github.com/flight505/storybook-assistant (marketplace companion)

---

## Maintenance Notes

### Critical Files (Never Delete)

- `.claude-plugin/plugin.json` - Plugin manifest
- `skills/common/http_client.py` - Core HTTP client
- `skills/diagram/scripts/generate_diagram.py` - Main CLI (wrapper)
- `skills/diagram/scripts/generate_diagram_ai.py` - AI generation logic
- `skills/image/scripts/generate_image.py` - Image generation/editing CLI
- `hooks/hooks.json` - Hook event declarations
- `hooks/validate-output.py` - PostToolUse output validation
- `commands/edit.md` - Edit command definition
- `commands/setup.md` - Setup command definition
- `CLAUDE.md` - Developer instructions
- `README.md` - Public documentation
- `CONTEXT_nano-banana.md` - This file (ground truth)

### Safe to Delete (Root Level)

**NONE** - All current root-level markdown files serve distinct purposes:
- `CLAUDE.md` - Developer instructions (keep)
- `README.md` - Public documentation (keep)
- `CHANGELOG.md` - Version history (keep)
- `CONTEXT_nano-banana.md` - Consolidated ground truth (new, keep)

### Skills Directory

**Keep as-is:**
- All `SKILL.md` files in `/skills/` subdirectories
- These are skill-specific reference docs (not consolidated)

---

## Summary

**Nano Banana** is a zero-dependency Claude Code plugin for AI-powered image and diagram generation. The plugin's core innovation is its stdlib-only HTTP client (v1.0.3), eliminating external dependencies and PEP 668 issues. It uses smart iteration with AI quality review to optimize costs while maintaining document-type-specific quality standards across 13 presets.

**Three skills** provide complementary capabilities: technical diagrams with quality review (`diagram`), general image generation/editing (`image`), and version-controlled text diagrams (`mermaid`). The plugin integrates with OpenRouter for unified API access to multiple AI models, primarily Gemini 3 Pro Image.

**v1.1.0** added iterative editing support via `/nano-banana:edit`, PostToolUse validation hooks for error recovery guidance, and skill hardening with `disable-model-invocation: true` to prevent unintended costly generation. Both diagram and image skills now support `--input` for editing existing files.

**Key architectural decisions** include zero external dependencies, threshold-based iteration vs. fixed iteration counts, document-type-aware quality standards, and explicit user control over generation invocation. The plugin is maintained in the flight505-marketplace ecosystem with webhook-based auto-updates.

---

**Document Version:** 2.0.0
**Last Updated:** 2026-02-16
**Maintained By:** flight505 (Jesper Vang)
