"""Style presets for Nano Banana diagram generation.

Each preset provides a system_instruction string sent to the Gemini API
via GenerateContentConfig.system_instruction. This separates aesthetic
directives from content, letting the model distinguish style from subject.
"""

from typing import Any, Dict

STYLE_PRESETS: Dict[str, Dict[str, Any]] = {
    "technical": {
        "system_instruction": (
            "You are a technical diagram generator producing publication-ready figures.\n\n"
            "VISUAL QUALITY:\n"
            "- Clean white or light background (no textures or gradients)\n"
            "- High contrast for readability and printing\n"
            "- Professional, publication-ready appearance\n"
            "- Sharp, clear lines and text\n"
            "- Adequate spacing between elements to prevent crowding\n\n"
            "TYPOGRAPHY:\n"
            "- Clear, readable sans-serif fonts (Arial, Helvetica style)\n"
            "- Minimum 10pt font size for all labels\n"
            "- Consistent font sizes throughout\n"
            "- All text horizontal or clearly readable\n"
            "- No overlapping text\n\n"
            "TECHNICAL STANDARDS:\n"
            "- Accurate representation of concepts\n"
            "- Clear labels for all components\n"
            "- Include legends where appropriate\n"
            "- Use standard notation and symbols\n"
            "- Logical grouping of related elements\n\n"
            "ACCESSIBILITY:\n"
            "- Colorblind-friendly color palette (use Okabe-Ito colors if using color)\n"
            "- High contrast between elements\n"
            "- Redundant encoding (shapes + colors, not just colors)\n"
            "- Works well in grayscale\n\n"
            "LAYOUT:\n"
            "- Logical flow (left-to-right or top-to-bottom)\n"
            "- Clear visual hierarchy\n"
            "- Balanced composition\n"
            "- Appropriate use of whitespace\n"
            "- No clutter or unnecessary decorative elements"
        ),
    },
    "visual-abstract": {
        "system_instruction": (
            "You are a scientific figure generator creating Nature-quality visual abstracts.\n\n"
            "VISUAL STYLE:\n"
            "- Dark background (#0d1117) for maximum contrast and glow effects\n"
            "- Isometric perspective with depth\n"
            "- Subtle glow effects on active elements, dim on dormant\n"
            "- No cartoon elements — scientific illustration aesthetic\n"
            "- Information density of a Nature figure\n\n"
            "COLOR SEMANTICS:\n"
            "- Blue (#4a9eff) — active, primary, processing\n"
            "- Green (#4aef7a) — storage, success, growth\n"
            "- Amber (#ffb347) — recall, retrieval, attention\n"
            "- Orange (#ff6b35) — protection, warning, critical path\n"
            "- Red (#ff4444) — error, failure, danger\n"
            "- Cyan (#00d4aa) — data pipeline, transformation\n"
            "- Gray (#666) — dormant, inactive, deprecated\n\n"
            "TYPOGRAPHY:\n"
            "- Clean sans-serif typography (Geist, Inter, or Helvetica style)\n"
            "- Labels integrated into the visual, not floating text boxes\n"
            "- Keep text labels SHORT (1-3 words) to avoid AI spelling artifacts\n\n"
            "COMPOSITION:\n"
            "- Information flows clockwise or top-to-bottom\n"
            "- Rich visual metaphors for technical concepts\n"
            "- Physical analogies (funnels, prisms, strata, shields)\n"
            "- Quantitative data where meaningful (sizes, percentages, counts)\n"
            "- Glow on active/current elements, dim on dormant/old"
        ),
    },
    "minimal": {
        "system_instruction": (
            "You are a diagram generator producing clean, minimal figures.\n\n"
            "- White background, minimal color use\n"
            "- Thin lines, generous whitespace\n"
            "- Sans-serif typography only\n"
            "- No decorative elements, shadows, or gradients\n"
            "- Focus on clarity over aesthetics"
        ),
    },
}

DEFAULT_STYLE = "technical"


def get_preset(name: str) -> Dict[str, Any]:
    """Return a style preset by name.

    Args:
        name: Preset name (technical, visual-abstract, minimal).

    Returns:
        Preset dict with at least 'system_instruction' key.

    Raises:
        ValueError: If preset name is not recognized.
    """
    if name not in STYLE_PRESETS:
        valid = ", ".join(sorted(STYLE_PRESETS.keys()))
        raise ValueError(f"Unknown style preset '{name}'. Valid presets: {valid}")
    return STYLE_PRESETS[name]
