# Changelog

All notable changes to Nano Banana will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.1] — 2026-03-12

### Fixed

- **Video: 4K resolution removed** — SDK only supports 720p and 1080p; 4K was never functional
- **Video: resolution not passed to API** — `resolution` field now included in `GenerateVideosConfig`
- **Video: reference images broken** — replaced file upload hack with native `VideoGenerationReferenceImage` SDK type (STYLE for 1, ASSET for 2-3)
- **Video: audio control via SDK** — added native `generate_audio` flag; ffmpeg kept as backup
- **Image: stale model ID** — `gemini-3-pro-image-preview` → `gemini-3.1-pro-image-preview` in all docs/examples
- **Diagram: defensive `response.text` access** — prevents `AttributeError` on non-text responses
- **Dead code removed** — unused `save_base64_image()` and `import base64` from image skill
- **Python version** — `requires-python` corrected to `>=3.10` (google-genai requires 3.10+)
- **Ruff target** — updated from `py38` to `py310`
- **Lint cleanup** — import sorting, extraneous f-string prefixes

---

## [3.0.0] — 2026-03-12

### Breaking Changes

- Dropped OpenRouter provider support — Google Gemini API only
- Removed `--provider` flag from image and diagram skills
- Requires `google-genai` Python SDK (`uv sync` or `pip install google-genai`)
- Model IDs updated to 3.1 versions

### Added

- **Video generation skill** — Veo 3.1 text-to-video, image-to-video, frame interpolation, video extension
- `skills/common/client.py` — shared google-genai client factory
- ffmpeg audio stripping for generated videos

### Changed

- Image skill migrated from urllib.request to google-genai SDK
- Diagram skill migrated from urllib.request to google-genai SDK
- Default image model: `gemini-3.1-flash-image-preview`
- Default diagram model: `gemini-3.1-pro-image-preview`
- Simplified provider architecture (single SDK, no fallback chain)

### Removed

- OpenRouter provider and all FLUX model support
- `--provider` CLI flag
- urllib.request HTTP client code

---

## [2.0.0] - 2026-03-02

### ⚠️ Breaking

- **Default image model changed** from `gemini-3-pro-image-preview` to `gemini-3.1-flash-image-preview` (Nano Banana 2 — faster, cheaper). Use `-m gemini-3-pro-image-preview` for the old default.
- Removed deprecated `gemini-2.5-flash-image-preview` references (model shut down)

### ✨ Added

- **Nano Banana 2** (`gemini-3.1-flash-image-preview`) — new default for image skill, fastest generation
- **`--aspect-ratio` flag** on image skill — 14 aspect ratios (1:1, 16:9, 9:16, 4:3, 21:9, etc.)
- **`--resolution` flag** on image and diagram skills — 512px, 1K, 2K, 4K
- **`imageConfig` API support** — sends `aspectRatio` and `imageSize` to Gemini API via `generationConfig.imageConfig`
- **Kroki skill** — render 27 text-based diagram types (Mermaid, PlantUML, GraphViz, D2, Excalidraw, BPMN, etc.) to PNG/SVG/PDF via [Kroki.io](https://kroki.io)
- **`gemini` and `kroki` keywords** added to plugin.json

### 🗑️ Removed

- **Mermaid skill** — replaced by kroki skill (broader coverage: 27 diagram types with actual rendering to PNG/SVG)

### 🔄 Changed

- **Image skill** defaults to Nano Banana 2 (Flash) for speed
- **Diagram skill** keeps Nano Banana Pro for highest quality output
- Updated all documentation with new model hierarchy and naming

---

## [1.3.2] - 2026-02-24

### 🐛 Fixed

- **OpenRouter 401 with explicit `--provider openrouter`** - Diagram wrapper passed GEMINI_API_KEY to OpenRouter when both keys were set
- **OpenRouter images saved as JPEG** - `save_base64_image()` now converts to PNG when output path is `.png`
- **API key routing hardened** - `generate_diagram_ai.py` rejects non-`sk-or-` keys for OpenRouter branch

---

## [1.3.0] - 2026-02-20

### ✨ Added

- **Google Gemini API Direct Support** - Preferred provider with free tier, no proxy layer
- **Provider Auto-Detection** - Prefers `GEMINI_API_KEY`, falls back to `OPENROUTER_API_KEY`
- **`--provider` Flag** - Force `google` or `openrouter` on all scripts
- **Shared Utilities** - `skills/common/image_utils.py` and `skills/common/env.py` eliminate code duplication

### 🔄 Changed

- **Error Handling** - `generate_image.py` raises exceptions instead of calling `sys.exit()` (now importable as a library)
- **JPEG-to-PNG Conversion** - Automatic conversion when Google API returns JPEG for `.png` output
- **Env Loading** - Unified stdlib-only `.env` file loading (no `python-dotenv` needed)

### 🗑️ Removed

- **`http_client.py`** - Unused `OpenRouterClient` class deleted
- Dead `_is_png` method, unreachable code branches

### 🔧 Fixed

- `generate_diagram.py` wrapper now supports `GEMINI_API_KEY` (was hardcoded to OpenRouter only)
- Temp file leaks in `_convert_to_png` (proper `finally` cleanup)
- Wasted base64 encoding in `review_image()` for Google provider

### 📝 Documentation

- Updated SKILL.md files to reflect Google API as preferred provider
- Updated `setup.md` with dual-provider instructions
- Synced all version references to 1.3.0

---

## [1.0.3] - 2025-01-08

### 🔄 Changed

- **Zero Dependencies** - Rewrote HTTP layer to use Python stdlib (`urllib.request`) instead of `requests` library
- **PEP 668 Compatible** - Works on all modern Python environments without dependency installation issues
- **Simplified Setup** - No `pip install` step required - just configure API key and run!

### 🗑️ Removed

- Removed `requests` library dependency from `pyproject.toml` and `requirements.txt`
- Removed dependency installation instructions from setup command

### 📝 Documentation

- Updated README with zero-dependency highlight
- Simplified quick start guide (removed step 3: Install Dependencies)
- Updated setup.md with streamlined configuration instructions

---

## [1.0.2] - 2025-01-07

### ✨ Added

- **Logo** - Added Nano Banana logo to README (`assets/nano-banana-logo.png`)
- **README Styling** - Centered header with logo and badges for better presentation

---

## [1.0.1] - 2025-01-07

### 🔧 Fixed

- **Plugin Schema** - Fixed marketplace.json with required `owner` and `plugins` fields
- **Skills Format** - Changed plugin.json skills from objects to string paths
- **uv Deprecation** - Use `dependency-groups.dev` instead of deprecated `tool.uv.dev-dependencies`
- **Simplified Dependencies** - Focus on exported API keys (no .env dependency required)

---

## [1.0.0] - 2025-01-07

### 🎉 Initial Release

Standalone Claude Code plugin for AI-powered image and diagram generation, extracted from [Claude Project Planner](https://github.com/flight505/claude-project-planner).

### ✨ Features

#### Diagram Skill (`diagram`)

- **Nano Banana Pro Integration** - Uses Gemini 3 Pro Image for generation
- **Smart Iteration** - Only regenerates if quality below threshold (saves API calls)
- **AI Quality Review** - Gemini 3 Pro evaluates on 5 criteria:
  - Technical Accuracy
  - Clarity and Readability
  - Label Quality
  - Layout and Composition
  - Professional Appearance
- **13 Document Types** with specific quality thresholds:
  - `specification` (8.5), `architecture` (8.0), `proposal` (8.0)
  - `journal` (8.5), `conference` (8.0), `thesis` (8.0), `grant` (8.0)
  - `sprint` (7.5), `report` (7.5), `preprint` (7.5)
  - `readme` (7.0), `poster` (7.0), `presentation` (6.5)
  - `default` (7.5)
- **Review Log** - JSON output with scores and critiques

#### Image Skill (`image`)

- **Multiple Models** - Gemini 3 Pro Image, FLUX Pro, FLUX Flex
- **Image Generation** - Create images from text descriptions
- **Image Editing** - Modify existing images with natural language
- **Simple CLI** - One command for generation or editing

#### Mermaid Skill (`mermaid`)

- **Text-Based Diagrams** - Version-controllable diagram code
- **Wide Platform Support** - GitHub, GitLab, Notion, Obsidian
- **8 Diagram Types** documented:
  - Flowcharts
  - Sequence diagrams
  - Class diagrams
  - ERD diagrams
  - State diagrams
  - Gantt charts
  - Pie charts
  - Git graphs

### 📦 Plugin Infrastructure

- **Plugin Manifests** - plugin.json and marketplace.json
- **Setup Command** - `/nano-banana:setup` for configuration
- **Python Packaging** - pyproject.toml for uv/pip compatibility
- **Requirements** - requirements.txt for easy dependency installation

### 📝 Documentation

- Comprehensive SKILL.md for each skill
- README with quick start guide
- Setup command with step-by-step configuration

---

## Origin

Extracted from [Claude Project Planner](https://github.com/flight505/claude-project-planner) to provide standalone image/diagram generation capabilities for any Claude Code project.

**Key Improvements over Source:**

- Standalone plugin (no project planning dependencies)
- Cleaner branding (Nano Banana)
- Added `readme` document type (7.0 threshold)
- uv-compatible Python packaging
- Simplified directory structure

---

**Legend:**
- ✨ Added - New features
- 🔄 Changed - Changes in existing functionality
- 🗑️ Removed - Removed features
- 🔧 Fixed - Bug fixes
- 📝 Documentation - Documentation changes
