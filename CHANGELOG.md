# Changelog

All notable changes to Nano Banana will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
