---
description: Configure API keys and environment for Nano Banana
---

# Nano Banana Setup

I'll help you configure Nano Banana for image and diagram generation.

## Requirements Check

Nano Banana requires:
1. **OpenRouter API Key** - For accessing AI models (Gemini 3 Pro Image, FLUX, etc.)
2. **Python 3.8+** - With `requests` library installed

## Step 1: Check Current Configuration

Let me check if you already have the required configuration:

```bash
# Check for OPENROUTER_API_KEY
if [ -n "$OPENROUTER_API_KEY" ]; then
    echo "✅ OPENROUTER_API_KEY is set in environment"
else
    echo "❌ OPENROUTER_API_KEY not found in environment"
fi

# Check for .env file
if [ -f ".env" ] && grep -q "OPENROUTER_API_KEY" .env; then
    echo "✅ OPENROUTER_API_KEY found in .env file"
fi
```

## Step 2: Get Your OpenRouter API Key

If you don't have an OpenRouter API key:

1. Go to **https://openrouter.ai/keys**
2. Sign in or create an account
3. Click **"Create Key"**
4. Copy your API key (starts with `sk-or-v1-...`)
5. Add credits to your account

## Step 3: Configure API Key

Choose ONE of these methods:

### Option A: Environment Variable (Recommended for Development)

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export OPENROUTER_API_KEY='sk-or-v1-your-key-here'
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### Option B: Project .env File (Recommended for Projects)

Create a `.env` file in your project root:

```bash
echo "OPENROUTER_API_KEY=sk-or-v1-your-key-here" > .env
```

**Important:** Add `.env` to your `.gitignore`:
```bash
echo ".env" >> .gitignore
```

### Option C: Per-Command (For Testing)

Pass the key directly:
```bash
python generate_diagram.py "My diagram" -o diagram.png --api-key sk-or-v1-your-key-here
```

## Step 4: Install Python Dependencies

### With uv (Recommended)

```bash
# Install requests
uv pip install requests

# Optional: Install python-dotenv for .env file support
uv pip install python-dotenv
```

### With pip

```bash
pip install requests python-dotenv
```

### From requirements.txt

```bash
# In the nano-banana directory
pip install -r requirements.txt
# Or with uv
uv pip install -r requirements.txt
```

## Step 5: Verify Installation

Test that everything works:

```bash
# Test diagram generation
python skills/diagram/scripts/generate_diagram.py "Simple flowchart with start, process, and end boxes" -o test_diagram.png --doc-type presentation

# Test image generation
python skills/image/scripts/generate_image.py "A simple blue square" -o test_image.png
```

If successful, you'll see:
```
✅ Image saved to: test_diagram.png
```

## Configuration Summary

After setup, your configuration should look like:

| Component | Status |
|-----------|--------|
| OPENROUTER_API_KEY | ✅ Set (env or .env) |
| Python 3.8+ | ✅ Installed |
| requests library | ✅ Installed |
| python-dotenv | ✅ Installed (optional) |

## Troubleshooting

### "OPENROUTER_API_KEY not found"
- Ensure the environment variable is set: `echo $OPENROUTER_API_KEY`
- Or ensure `.env` file exists with the key
- Restart your terminal after adding to shell profile

### "requests library not found"
```bash
pip install requests
# or
uv pip install requests
```

### "Permission denied" on scripts
```bash
chmod +x skills/*/scripts/*.py
```

### API Errors
- Check your API key is correct
- Ensure you have credits in your OpenRouter account
- Check https://openrouter.ai/activity for usage and errors

## Next Steps

You're all set! Try these commands:

```bash
# Generate an architecture diagram
python skills/diagram/scripts/generate_diagram.py "Microservices architecture with 3 services and a database" -o architecture.png --doc-type architecture

# Generate a creative image
python skills/image/scripts/generate_image.py "A cozy coffee shop interior, warm lighting" -o coffee_shop.png

# Edit an existing image
python skills/image/scripts/generate_image.py "Add rain to the window" --input coffee_shop.png -o rainy_coffee_shop.png
```

See the skill documentation for more examples:
- `skills/diagram/SKILL.md` - Technical diagram generation
- `skills/image/SKILL.md` - Image generation and editing
- `skills/mermaid/SKILL.md` - Text-based diagrams
