---
description: Configure API keys and environment for Nano Banana
---

# Nano Banana Setup

I'll help you configure Nano Banana for image and diagram generation.

## Requirements

Nano Banana requires:
1. **Google Gemini API Key** (preferred) or **OpenRouter API Key** - For accessing AI models
2. **Python 3.8+** - Uses stdlib only, **no external dependencies required!**

## Step 1: Check Current Configuration

Let me check if you already have the required configuration:

```bash
# Check for GEMINI_API_KEY (preferred)
if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ GEMINI_API_KEY is set (Google direct API - preferred)"
elif [ -n "$OPENROUTER_API_KEY" ]; then
    echo "✅ OPENROUTER_API_KEY is set (OpenRouter fallback)"
else
    echo "❌ No API key found"
fi
```

## Step 2: Get Your API Key

### Option 1: Google Gemini API Key (Recommended)

The Google Gemini API is **preferred** because:
- Free tier available (generous limits)
- Direct connection (no proxy layer)
- Most reliable for image generation

1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy your API key

### Option 2: OpenRouter API Key (Alternative)

Use OpenRouter if you need access to non-Google models (FLUX, etc.):

1. Go to **https://openrouter.ai/keys**
2. Sign in or create an account
3. Click **"Create Key"**
4. Copy your API key (starts with `sk-or-v1-...`)
5. Add credits to your account

## Step 3: Configure API Key

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Preferred: Google Gemini direct API (free tier)
export GEMINI_API_KEY='your-gemini-key-here'

# Alternative: OpenRouter (supports FLUX and other non-Google models)
# export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
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

## Step 4: Verify Installation

**No dependency installation required!** Nano Banana uses Python stdlib only.

Test that everything works:

```bash
# Test diagram generation
python3 skills/diagram/scripts/generate_diagram_ai.py "Simple flowchart with start, process, and end boxes" -o test_diagram.png --doc-type presentation -v

# Test image generation
python3 skills/image/scripts/generate_image.py "A simple blue square" -o test_image.png
```

If successful, you'll see the provider being used and the saved output path.

## Configuration Summary

| Component | Status |
|-----------|--------|
| GEMINI_API_KEY | ✅ Preferred (free tier, direct) |
| OPENROUTER_API_KEY | ⚡ Alternative (multi-model) |
| Python 3.8+ | ✅ Installed |
| External dependencies | ✅ None required! |

**Provider auto-detection:** When both keys are set, Nano Banana prefers the Google direct API. Use `--provider openrouter` to force OpenRouter.

## Optional: .env File Support

If you want to use `.env` files, install python-dotenv:

```bash
pip install python-dotenv
# or
uv pip install python-dotenv
```

This is **optional** - you can also just use exported environment variables.

## Troubleshooting

### "No API key found"
- Ensure at least one key is set: `echo $GEMINI_API_KEY` or `echo $OPENROUTER_API_KEY`
- Or ensure `.env` file exists with the key
- Restart your terminal after adding to shell profile

### "Permission denied" on scripts
```bash
chmod +x skills/*/scripts/*.py
```

### API Errors
- Check your API key is correct
- For Google: check https://aistudio.google.com for quota/usage
- For OpenRouter: check https://openrouter.ai/activity for usage and errors

## Next Steps

You're all set! Try these commands:

```bash
# Generate an architecture diagram
python3 skills/diagram/scripts/generate_diagram_ai.py "Microservices architecture with 3 services and a database" -o architecture.png --doc-type architecture

# Generate a creative image
python3 skills/image/scripts/generate_image.py "A cozy coffee shop interior, warm lighting" -o coffee_shop.png

# Edit an existing image
python3 skills/image/scripts/generate_image.py "Add rain to the window" --input coffee_shop.png -o rainy_coffee_shop.png

# Force a specific provider
python3 skills/image/scripts/generate_image.py "A sunset" -o sunset.png --provider google
```

See the skill documentation for more examples:
- `skills/diagram/SKILL.md` - Technical diagram generation
- `skills/image/SKILL.md` - Image generation and editing
- `skills/mermaid/SKILL.md` - Text-based diagrams
