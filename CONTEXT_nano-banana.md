# CONTEXT_nano-banana.md

## Ground Truth Documentation

**Plugin:** Nano Banana
**Version:** 1.0.5
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
3. If score < threshold: regenerate (max 3 iterations)
4. If score ≥ threshold: stop early (saves API calls)

**Quality Criteria:**
- Technical Accuracy (0-10)
- Clarity and Readability (0-10)
- Label Quality (0-10)
- Layout and Composition (0-10)
- Professional Appearance (0-10)

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
   - Model ID: `google/gemini-3-pro`
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
User Description
    ↓
generate_diagram.py
    ↓
OpenRouterClient (stdlib HTTP)
    ↓
Gemini 3 Pro Image (generate diagram)
    ↓
Base64 image response
    ↓
Gemini 3 Pro (quality review)
    ↓
Score >= threshold? → Save and exit
Score < threshold? → Regenerate (max 3 iterations)
```

---

## File Structure and Organization

### Root Structure

```
nano-banana/
├── .claude-plugin/
│   └── plugin.json              # Plugin manifest (v1.0.5)
├── .github/
│   └── workflows/
│       └── notify-marketplace.yml  # Webhook to marketplace
├── assets/
│   └── nano-banana-hero-voxel.png  # Hero image
├── commands/
│   └── setup.md                 # /nano-banana:setup command
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
   - `python skills/diagram/scripts/generate_diagram.py`
   - No package installation required

3. **SKILL.md** files - Skill-specific documentation
   - Stay in `/skills/` directory (not consolidated)
   - Reference documentation for each skill

4. **Zero dependencies** - `requirements.txt` is empty
   - Only `python-dotenv` in optional dependencies (for dev)
   - `pyproject.toml` declares no required dependencies

---

## Version History and Major Changes

### v1.0.5 (2026-01-13) - Current
- Latest stable release in marketplace

### v1.0.4 (2025-01-10)
- Documentation improvements
- Badge updates

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
python skills/diagram/scripts/generate_diagram.py \
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
| Complex/high threshold (3 iterations) | 3 | $0.15-0.30 |

**Cost Breakdown:**
- Diagram generation: ~$0.03-0.08 per image
- Quality review: ~$0.01-0.02 per review
- Total per iteration: ~$0.05-0.10

**Smart Iteration Savings:**
- Without smart iteration (fixed 3 iterations): $0.15-0.30
- With smart iteration (early stopping): $0.05-0.20
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
  "version": "1.0.5",
  "author": {
    "name": "Jesper Vang",
    "url": "https://github.com/flight505"
  },
  "source": "./nano-banana",
  "category": "productivity",
  "keywords": ["image-generation", "diagram", "ai", "visualization"]
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
- No vector output (SVG) support

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

3. **Vector Output**
   - Add SVG export option
   - Scalable diagrams for presentations

4. **Local Model Support**
   - Optional local model fallback
   - Privacy-sensitive use cases

5. **Custom Quality Criteria**
   - User-defined review criteria
   - Domain-specific quality metrics

### Known Issues

1. **Timeout on Complex Diagrams**
   - Very complex diagrams may timeout (>120s)
   - Workaround: Increase timeout or simplify description

2. **No Progress Indication**
   - CLI doesn't show progress during generation
   - Can feel unresponsive for 30-60 second generations

3. **No Diagram History**
   - No built-in way to track previous generations
   - Users must manage output files manually

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
- `skills/diagram/scripts/generate_diagram.py` - Main CLI
- `skills/diagram/scripts/generate_diagram_ai.py` - AI logic
- `skills/image/scripts/generate_image.py` - Image CLI
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

**Key architectural decisions** include zero external dependencies, threshold-based iteration vs. fixed iteration counts, and document-type-aware quality standards. The plugin is maintained in the flight505-marketplace ecosystem with webhook-based auto-updates.

---

**Document Version:** 1.0.0
**Last Updated:** 2026-01-13
**Maintained By:** flight505 (Jesper Vang)
