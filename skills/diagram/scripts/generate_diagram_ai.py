#!/usr/bin/env python3
"""
AI-powered diagram generation using Nano Banana Pro.

This script uses a smart iterative refinement approach:
1. Generate initial diagram with Nano Banana Pro (Gemini 3.1 Pro Image) for highest quality
2. AI quality review using Gemini 3.1 Pro for professional critique
3. Only regenerate if quality is below threshold for document type
4. Repeat until quality meets standards (max iterations)

Requirements:
    - google-genai>=1.0.0
    - GEMINI_API_KEY environment variable
    - Python 3.10+

Usage:
    python generate_diagram_ai.py "Create a flowchart showing user authentication flow" -o flowchart.png
    python generate_diagram_ai.py "System architecture diagram for microservices" -o architecture.png --doc-type architecture
    python generate_diagram_ai.py "Simple block diagram" -o diagram.png --doc-type presentation
    python generate_diagram_ai.py "Wide architecture overview" -o arch.png --resolution 2K
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Add skills/ to path for common imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from common.client import get_client  # noqa: E402
from common.image_utils import convert_to_png, get_mime_type  # noqa: E402
from google.genai import types  # noqa: E402


class NanoBananaGenerator:
    """Generate diagrams using Nano Banana Pro with smart iterative refinement.

    Uses Gemini 3.1 Pro for quality review to determine if regeneration is needed.
    Multiple passes only occur if the generated diagram doesn't meet the
    quality threshold for the target document type.
    """

    # Quality thresholds by document type (score out of 10)
    QUALITY_THRESHOLDS = {
        # Technical/Project doc types
        "specification": 8.5,  # Technical specs, PRDs - highest standards
        "architecture": 8.0,   # Architecture documents - high standards
        "proposal": 8.0,       # Business proposals - must be compelling
        "sprint": 7.5,         # Sprint planning docs - professional
        "readme": 7.0,         # README files - good quality
        # Academic/Scientific doc types
        "journal": 8.5,        # Nature, Science, etc. - highest standards
        "conference": 8.0,     # Conference papers - high standards
        "poster": 7.0,         # Academic posters - good quality
        "presentation": 6.5,   # Slides/talks - clear but less formal
        "report": 7.5,         # Technical reports - professional
        "grant": 8.0,          # Grant proposals - must be compelling
        "thesis": 8.0,         # Dissertations - formal academic
        "preprint": 7.5,       # arXiv, etc. - good quality
        "default": 7.5,        # Default threshold
    }

    # Diagram generation guidelines
    DIAGRAM_GUIDELINES = """
Create a high-quality technical diagram with these requirements:

VISUAL QUALITY:
- Clean white or light background (no textures or gradients)
- High contrast for readability and printing
- Professional, publication-ready appearance
- Sharp, clear lines and text
- Adequate spacing between elements to prevent crowding

TYPOGRAPHY:
- Clear, readable sans-serif fonts (Arial, Helvetica style)
- Minimum 10pt font size for all labels
- Consistent font sizes throughout
- All text horizontal or clearly readable
- No overlapping text

TECHNICAL STANDARDS:
- Accurate representation of concepts
- Clear labels for all components
- Include legends where appropriate
- Use standard notation and symbols
- Logical grouping of related elements

ACCESSIBILITY:
- Colorblind-friendly color palette (use Okabe-Ito colors if using color)
- High contrast between elements
- Redundant encoding (shapes + colors, not just colors)
- Works well in grayscale

LAYOUT:
- Logical flow (left-to-right or top-to-bottom)
- Clear visual hierarchy
- Balanced composition
- Appropriate use of whitespace
- No clutter or unnecessary decorative elements
"""

    def __init__(self, api_key: Optional[str] = None, verbose: bool = False,
                 timeout: int = 120, resolution: Optional[str] = None):
        """
        Initialize the generator.

        Args:
            api_key: Gemini API key (or set GEMINI_API_KEY env var)
            verbose: Print detailed progress information
            timeout: Request timeout in seconds (default: 120)
            resolution: Image resolution (512px, 1K, 2K, 4K)
        """
        self.verbose = verbose
        self.timeout = timeout
        self.resolution = resolution
        self._last_error = None

        self.client = get_client(api_key)
        self.image_model = "gemini-3-pro-image-preview"
        self.review_model = "gemini-3.1-pro-preview"

        self._log(f"Image model: {self.image_model}")

    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")

    @staticmethod
    def _convert_to_png(data: bytes) -> bytes:
        """Convert image bytes to PNG format if needed."""
        return convert_to_png(data)

    def generate_image(self, prompt: str, input_image: Optional[str] = None) -> Optional[bytes]:
        """Generate an image using Nano Banana Pro.

        Args:
            prompt: The generation prompt describing the desired diagram.
            input_image: Optional path to an existing image to edit.
                         When provided, the image is sent alongside the prompt
                         so the model can modify it rather than generating from scratch.
        """
        self._last_error = None

        try:
            parts: list = [prompt]

            if input_image:
                with open(input_image, "rb") as f:
                    img_bytes = f.read()
                mime = get_mime_type(input_image)
                parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))

            config_kwargs: Dict[str, Any] = {
                "response_modalities": ["TEXT", "IMAGE"],
            }
            if self.resolution:
                config_kwargs["image_config"] = types.ImageConfig(
                    image_size=self.resolution,
                )

            response = self.client.models.generate_content(
                model=self.image_model,
                contents=parts,
                config=types.GenerateContentConfig(**config_kwargs),
            )

            # Extract image bytes from response
            if response.parts:
                for part in response.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        image_data = part.inline_data.data
                        self._log(f"Generated image ({len(image_data)} bytes)")
                        return image_data

            self._last_error = "No image data in API response"
            self._log("No image found in response")
            return None

        except Exception as e:
            self._last_error = str(e)
            self._log(f"Generation failed: {self._last_error}")
            return None

    def review_image(self, image_path: str, original_prompt: str,
                    iteration: int, doc_type: str = "default",
                    max_iterations: int = 2) -> Tuple[str, float, bool]:
        """Review generated image using Gemini 3.1 Pro for quality analysis."""
        threshold = self.QUALITY_THRESHOLDS.get(doc_type.lower(),
                                                 self.QUALITY_THRESHOLDS["default"])

        review_prompt = f"""You are an expert reviewer evaluating a technical diagram for publication quality.

ORIGINAL REQUEST: {original_prompt}

DOCUMENT TYPE: {doc_type} (quality threshold: {threshold}/10)
ITERATION: {iteration}/{max_iterations}

Evaluate this diagram on these criteria:

1. **Technical Accuracy** (0-2 points) - Correct representation of concepts
2. **Clarity and Readability** (0-2 points) - Easy to understand at a glance
3. **Label Quality** (0-2 points) - All elements labeled, readable fonts
4. **Layout and Composition** (0-2 points) - Logical flow, balanced space
5. **Professional Appearance** (0-2 points) - Publication-ready quality

RESPOND IN THIS EXACT FORMAT:
SCORE: [total score 0-10]

STRENGTHS:
- [strength 1]
- [strength 2]

ISSUES:
- [issue 1 if any]
- [issue 2 if any]

VERDICT: [ACCEPTABLE or NEEDS_IMPROVEMENT]

If score >= {threshold}, the diagram is ACCEPTABLE for {doc_type}.
If score < {threshold}, mark as NEEDS_IMPROVEMENT with specific suggestions."""

        try:
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            mime = get_mime_type(image_path)

            response = self.client.models.generate_content(
                model=self.review_model,
                contents=[
                    review_prompt,
                    types.Part.from_bytes(data=img_bytes, mime_type=mime),
                ],
            )

            content = getattr(response, "text", None) or ""

            # Extract score
            score = 7.5
            score_match = re.search(r'SCORE:\s*(\d+(?:\.\d+)?)', content, re.IGNORECASE)
            if score_match:
                score = float(score_match.group(1))
            else:
                score_match = re.search(r'(?:score|rating|quality)[:\s]+(\d+(?:\.\d+)?)', content, re.IGNORECASE)
                if score_match:
                    score = float(score_match.group(1))

            needs_improvement = False
            if "NEEDS_IMPROVEMENT" in content.upper():
                needs_improvement = True
            elif score < threshold:
                needs_improvement = True

            self._log(f"Review complete (Score: {score}/10, Threshold: {threshold}/10)")

            return (content if content else "Image generated successfully", score, needs_improvement)
        except Exception as e:
            self._log(f"Review skipped: {str(e)}")
            return "Image generated successfully (review skipped)", 7.5, False

    def improve_prompt(self, original_prompt: str, critique: str, iteration: int) -> str:
        """Improve the generation prompt based on critique."""
        return f"""{self.DIAGRAM_GUIDELINES}

USER REQUEST: {original_prompt}

ITERATION {iteration}: Based on previous feedback, address these specific improvements:
{critique}

Generate an improved version that addresses all the critique points while maintaining technical accuracy and professional quality."""

    def generate_iterative(self, user_prompt: str, output_path: str,
                          iterations: int = 2,
                          doc_type: str = "default",
                          input_image: Optional[str] = None) -> Dict[str, Any]:
        """Generate diagram with smart iterative refinement.

        Args:
            user_prompt: Description of the diagram to generate or edit instructions.
            output_path: File path for the output image.
            iterations: Maximum number of refinement iterations.
            doc_type: Document type for quality threshold selection.
            input_image: Optional path to an existing diagram to edit.
        """
        out = Path(output_path)
        output_dir = out.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = out.stem
        extension = out.suffix or ".png"

        threshold = self.QUALITY_THRESHOLDS.get(doc_type.lower(),
                                                 self.QUALITY_THRESHOLDS["default"])

        results = {
            "user_prompt": user_prompt,
            "doc_type": doc_type,
            "quality_threshold": threshold,
            "iterations": [],
            "final_image": None,
            "final_score": 0.0,
            "success": False,
            "early_stop": False,
            "early_stop_reason": None
        }

        is_editing = input_image is not None

        if is_editing:
            current_prompt = f"""{self.DIAGRAM_GUIDELINES}

EDITING MODE: Modify the provided diagram based on these instructions.
Keep all existing elements unless the user explicitly asks to remove them.

USER EDIT REQUEST: {user_prompt}

Generate the updated diagram maintaining publication quality."""
        else:
            current_prompt = f"""{self.DIAGRAM_GUIDELINES}

USER REQUEST: {user_prompt}

Generate a publication-quality technical diagram that meets all the guidelines above."""

        print(f"\n{'='*60}")
        print(f"Nano Banana - {'Editing' if is_editing else 'Generating'} Diagram")
        print(f"{'='*60}")
        if is_editing:
            print(f"Source: {input_image}")
            print(f"Edit: {user_prompt}")
        else:
            print(f"Description: {user_prompt}")
        print(f"Model: {self.image_model}")
        print(f"Document Type: {doc_type}")
        print(f"Quality Threshold: {threshold}/10")
        print(f"Max Iterations: {iterations}")
        print(f"Timeout: {self.timeout}s")
        print(f"Output: {output_path}")
        print(f"{'='*60}\n")

        total_start = time.time()

        for i in range(1, iterations + 1):
            print(f"\n[Iteration {i}/{iterations}]")
            print("-" * 40)

            action = 'Editing' if is_editing and i == 1 else 'Generating'
            print(f"{action} diagram...")
            t_gen = time.time()
            image_data = self.generate_image(current_prompt, input_image=input_image if i == 1 else None)
            gen_elapsed = time.time() - t_gen

            if not image_data:
                error_msg = getattr(self, '_last_error', 'Image generation failed')
                print(f"Generation failed: {error_msg} (after {gen_elapsed:.1f}s)")
                results["iterations"].append({
                    "iteration": i,
                    "success": False,
                    "error": error_msg
                })
                continue

            # Convert to PNG if output requests .png
            if extension.lower() == ".png":
                image_data = self._convert_to_png(image_data)

            iter_path = output_dir / f"{base_name}_v{i}{extension}"
            with open(iter_path, "wb") as f:
                f.write(image_data)
            print(f"Saved: {iter_path} (elapsed: {gen_elapsed:.1f}s)")

            print(f"Reviewing with {self.review_model}...")
            t_review = time.time()
            critique, score, needs_improvement = self.review_image(
                str(iter_path), user_prompt, i, doc_type, iterations
            )
            review_elapsed = time.time() - t_review
            print(f"Score: {score}/10 (threshold: {threshold}/10) (review: {review_elapsed:.1f}s)")

            iteration_result = {
                "iteration": i,
                "image_path": str(iter_path),
                "prompt": current_prompt,
                "critique": critique,
                "score": score,
                "needs_improvement": needs_improvement,
                "success": True
            }
            results["iterations"].append(iteration_result)

            if not needs_improvement:
                print(f"\nQuality meets {doc_type} threshold ({score} >= {threshold})")
                print("  No further iterations needed!")
                results["final_image"] = str(iter_path)
                results["final_score"] = score
                results["success"] = True
                results["early_stop"] = True
                results["early_stop_reason"] = f"Quality score {score} meets threshold {threshold} for {doc_type}"
                break

            if i == iterations:
                print("\nMaximum iterations reached")
                results["final_image"] = str(iter_path)
                results["final_score"] = score
                results["success"] = True
                break

            print(f"\nQuality below threshold ({score} < {threshold})")
            print("Improving prompt based on feedback...")
            current_prompt = self.improve_prompt(user_prompt, critique, i + 1)

        # Copy final version to output path
        if results["success"] and results["final_image"]:
            final_iter_path = Path(results["final_image"])
            if final_iter_path != Path(output_path):
                shutil.copy(final_iter_path, output_path)
                print(f"\nFinal image: {output_path}")

        # Save review log
        log_path = output_dir / f"{base_name}_review_log.json"
        with open(log_path, "w") as f:
            json.dump(results, f, indent=2)
        print(f"Review log: {log_path}")

        total_elapsed = time.time() - total_start

        print(f"\n{'='*60}")
        print("Nano Banana - Generation Complete")
        print(f"Final Score: {results['final_score']}/10")
        if results["early_stop"]:
            print(f"Iterations Used: {len([r for r in results['iterations'] if r.get('success')])}/{iterations} (early stop)")
        print(f"Total Time: {total_elapsed:.1f}s")
        print(f"{'='*60}\n")

        return results


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate diagrams using Nano Banana Pro with smart iterative refinement",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate architecture diagram
  python generate_diagram_ai.py "Microservices architecture with API gateway" -o architecture.png --doc-type architecture

  # Generate flowchart for presentation (lower threshold, faster)
  python generate_diagram_ai.py "User authentication flow" -o auth_flow.png --doc-type presentation

  # Generate with higher resolution
  python generate_diagram_ai.py "Complex system diagram" -o system.png --resolution 2K

  # Generate with verbose output
  python generate_diagram_ai.py "Database schema for e-commerce" -o schema.png -v

Document Types (quality thresholds):
  specification 8.5/10 - Technical specs, PRDs
  architecture  8.0/10 - Architecture documents
  proposal      8.0/10 - Business proposals
  journal       8.5/10 - Academic journals
  conference    8.0/10 - Conference papers
  thesis        8.0/10 - Dissertations
  grant         8.0/10 - Grant proposals
  sprint        7.5/10 - Sprint planning docs
  report        7.5/10 - Technical reports
  preprint      7.5/10 - Preprints
  readme        7.0/10 - README files
  poster        7.0/10 - Academic posters
  presentation  6.5/10 - Slides, talks
  default       7.5/10 - General purpose

Model:
  Diagrams use Nano Banana Pro (gemini-3-pro-image-preview) for highest quality.
  Quality review uses Gemini 3.1 Pro (gemini-3.1-pro-preview).

Resolutions:
  512px, 1K, 2K, 4K

Note: Multiple iterations only occur if quality is BELOW the threshold.
      If the first generation meets the threshold, no extra API calls are made.

Environment:
  GEMINI_API_KEY        Google Gemini API key (free tier at aistudio.google.com)
        """
    )

    parser.add_argument("prompt", help="Description of the diagram to generate")
    parser.add_argument("-o", "--output", required=True,
                       help="Output image path (e.g., diagram.png)")
    parser.add_argument("--iterations", type=int, default=2,
                       help="Maximum refinement iterations (default: 2, max: 2)")
    parser.add_argument("--doc-type", default="default",
                       choices=list(NanoBananaGenerator.QUALITY_THRESHOLDS.keys()),
                       help="Document type for quality threshold (default: default)")
    parser.add_argument("--input", "-i", type=str,
                       help="Input diagram image to edit (enables edit mode)")
    parser.add_argument("--resolution", type=str,
                       choices=["512px", "1K", "2K", "4K"],
                       help="Image resolution (512px, 1K, 2K, 4K)")
    parser.add_argument("--api-key", help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--timeout", type=int, default=120,
                       help="Request timeout in seconds (default: 120)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()

    if args.iterations < 1 or args.iterations > 2:
        print("Error: Iterations must be between 1 and 2")
        sys.exit(1)

    if args.input and not os.path.exists(args.input):
        print(f"Error: Input image not found: {args.input}")
        sys.exit(1)

    try:
        generator = NanoBananaGenerator(
            api_key=args.api_key, verbose=args.verbose,
            timeout=args.timeout, resolution=args.resolution
        )
        results = generator.generate_iterative(
            user_prompt=args.prompt,
            output_path=args.output,
            iterations=args.iterations,
            doc_type=args.doc_type,
            input_image=args.input
        )

        if results["success"]:
            print(f"\nSuccess! Image saved to: {args.output}")
            sys.exit(0)
        else:
            print("\nGeneration failed. Check review log for details.")
            sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
