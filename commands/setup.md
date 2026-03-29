---
description: Configure API keys and environment for Nano Banana
---

# Nano Banana Setup

I'll help you configure Nano Banana for image, diagram, and video generation.

## Requirements

Nano Banana requires:
1. **Google Gemini API Key** - For accessing Gemini image and video models
2. **Python 3.10+** - Required for `google-genai` SDK
3. **google-genai SDK** - Install via `uv sync` or `pip install google-genai`
4. **ffmpeg** (optional) - For stripping audio from generated videos

## Step 1: Check Current Configuration

Let me check if you already have the required configuration:

```bash
# Check for GEMINI_API_KEY
if [ -n "$GEMINI_API_KEY" ]; then
    echo "GEMINI_API_KEY is set"
else
    echo "No GEMINI_API_KEY found"
fi

# Check for google-genai SDK
python3 -c "import google.genai" 2>/dev/null && echo "google-genai SDK installed" || echo "google-genai SDK not found — run: uv sync or pip install google-genai"

# Check for ffmpeg (optional, for video audio stripping)
command -v ffmpeg >/dev/null && echo "ffmpeg available" || echo "ffmpeg not found (optional — needed for stripping audio from videos)"
```

## Step 2: Get Your API Key

### Google Gemini API Key

1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your API key

**Note:** Video generation (Veo 3.1) requires a **paid** Gemini API tier. Image and diagram generation work on the free tier.

## Step 3: Configure API Key

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export GEMINI_API_KEY='your-gemini-key-here'
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

You can also use a `.env` file in your project root:
```bash
echo "GEMINI_API_KEY=your-gemini-key-here" > .env
echo ".env" >> .gitignore
```

## Step 4: Install Dependencies

The `google-genai` SDK is required for all generation tasks:

```bash
# With uv (recommended)
uv sync

# Or with pip
pip install google-genai
```

## Step 5: Verify Installation

Test that everything works:

```bash
# Test diagram generation
python3 skills/diagram/scripts/generate_diagram.py "Simple flowchart with start, process, and end boxes" -o test_diagram.png --doc-type presentation -v

# Test image generation
python3 skills/image/scripts/generate_image.py "A simple blue square" -o test_image.png
```

If successful, you'll see the provider being used and the saved output path.

## Configuration Summary

| Component | Status |
|-----------|--------|
| GEMINI_API_KEY | Required (free tier for images, paid for video) |
| google-genai SDK | Required (`uv sync` or `pip install google-genai`) |
| Python 3.10+ | Required |
| ffmpeg | Optional (video audio stripping) |

## .env File Support

Nano Banana reads `.env` files automatically. Just create a `.env` in your project root:

```bash
echo "GEMINI_API_KEY=your-key-here" > .env
echo ".env" >> .gitignore
```

The plugin searches for `.env` files in the current directory and up to 5 parent directories.

## Troubleshooting

### "No API key found"
- Ensure GEMINI_API_KEY is set: `echo $GEMINI_API_KEY`
- Or ensure `.env` file exists with the key
- Restart your terminal after adding to shell profile

### "Permission denied" on scripts
```bash
chmod +x skills/*/scripts/*.py
```

### API Errors
- Check your API key is correct
- Check https://aistudio.google.com for quota/usage

### Video Generation Errors
- Video generation requires a paid Gemini API tier
- Videos can take 1-3 minutes to generate — be patient
- If audio stripping fails, install ffmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)

## Next Steps

You're all set! Try these commands:

```bash
# Generate an architecture diagram
python3 skills/diagram/scripts/generate_diagram.py "Microservices architecture with 3 services and a database" -o architecture.png --doc-type architecture

# Generate a creative image
python3 skills/image/scripts/generate_image.py "A cozy coffee shop interior, warm lighting" -o coffee_shop.png

# Edit an existing image
python3 skills/image/scripts/generate_image.py "Add rain to the window" --input coffee_shop.png -o rainy_coffee_shop.png
```

See the skill documentation for more examples:
- `skills/diagram/SKILL.md` - Technical diagram generation
- `skills/image/SKILL.md` - Image generation and editing
- `skills/kroki/SKILL.md` - Text-based diagram rendering (27 types via Kroki.io)
- `skills/video/SKILL.md` - AI video generation with Veo 3.1
