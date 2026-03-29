#!/usr/bin/env python3
"""
AI-powered diagram generation using Nano Banana Pro.

Smart iterative refinement:
1. Generate diagram with Nano Banana Pro via multi-turn chat
2. AI quality review using Gemini 3.1 Pro
3. Send critique back into the chat for context-aware refinement
4. Repeat until quality meets threshold (max iterations)

Style presets (--style):
  technical        White background, accessible, standard diagrams (default)
  visual-abstract  Dark background, glow, metaphors, Nature-quality figures
  minimal          White background, thin lines, no decoration

Requirements:
    - google-genai>=1.0.0
    - GEMINI_API_KEY environment variable
    - Python 3.10+

Usage:
    python generate_diagram.py "Microservices architecture" -o arch.png --doc-type architecture
    python generate_diagram.py "System as routing prism" -o visual.png --style visual-abstract --doc-type journal
    python generate_diagram.py "Simple block diagram" -o diagram.png --doc-type presentation
    python generate_diagram.py "Wide overview" -o wide.png --resolution 2K --aspect-ratio 16:9
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
from common.presets import DEFAULT_STYLE, STYLE_PRESETS, get_preset  # noqa: E402
from google.genai import types  # noqa: E402


class NanoBananaGenerator:
    """Generate diagrams using Nano Banana Pro with smart iterative refinement.

    Style directives are sent via system_instruction (not concatenated into the
    user prompt), keeping content separate from aesthetics. Iterative refinement
    uses multi-turn chat so the model retains context across iterations.
    """

    QUALITY_THRESHOLDS = {
        "specification": 8.5,
        "architecture": 8.0,
        "proposal": 8.0,
        "sprint": 7.5,
        "readme": 7.0,
        "journal": 8.5,
        "conference": 8.0,
        "poster": 7.0,
        "presentation": 6.5,
        "report": 7.5,
        "grant": 8.0,
        "thesis": 8.0,
        "preprint": 7.5,
        "default": 7.5,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        verbose: bool = False,
        timeout: int = 120,
        resolution: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        style: str = DEFAULT_STYLE,
    ):
        """
        Initialize the generator.

        Args:
            api_key: Gemini API key (or set GEMINI_API_KEY env var)
            verbose: Print detailed progress information
            timeout: Request timeout in seconds (default: 120)
            resolution: Image resolution (512, 1K, 2K, 4K)
            aspect_ratio: Image aspect ratio (e.g. 16:9, 1:1, 4:3)
            style: Style preset name (technical, visual-abstract, minimal)
        """
        self.verbose = verbose
        self.timeout = timeout
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio
        self.style = style
        self._last_error: Optional[str] = None

        self.client = get_client(api_key)
        self.image_model = "gemini-3-pro-image-preview"
        self.review_model = "gemini-3.1-pro-preview"

        self._preset = get_preset(style)

        self._log(f"Image model: {self.image_model}")
        self._log(f"Style: {style}")

    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{time.strftime('%H:%M:%S')}] {message}")

    @staticmethod
    def _convert_to_png(data: bytes) -> bytes:
        """Convert image bytes to PNG format if needed."""
        return convert_to_png(data)

    def _build_config(self) -> types.GenerateContentConfig:
        """Build GenerateContentConfig with system_instruction and image settings."""
        config_kwargs: Dict[str, Any] = {
            "response_modalities": ["TEXT", "IMAGE"],
            "system_instruction": self._preset["system_instruction"],
        }
        image_config_kwargs: Dict[str, str] = {}
        if self.resolution:
            image_config_kwargs["image_size"] = self.resolution
        if self.aspect_ratio:
            image_config_kwargs["aspect_ratio"] = self.aspect_ratio
        if image_config_kwargs:
            config_kwargs["image_config"] = types.ImageConfig(**image_config_kwargs)
        return types.GenerateContentConfig(**config_kwargs)

    @staticmethod
    def _extract_image(response: Any) -> Optional[bytes]:
        """Extract image bytes from a GenerateContentResponse."""
        if response.parts:
            for part in response.parts:
                if part.inline_data and part.inline_data.mime_type and \
                        part.inline_data.mime_type.startswith("image/"):
                    return part.inline_data.data
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

    def generate_iterative(self, user_prompt: str, output_path: str,
                          iterations: int = 2,
                          doc_type: str = "default",
                          input_image: Optional[str] = None) -> Dict[str, Any]:
        """Generate diagram with smart iterative refinement via multi-turn chat.

        Style directives are sent via system_instruction. The generation model
        retains context across iterations via chat, so critiques build on the
        model's own prior output rather than starting fresh.

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

        results: Dict[str, Any] = {
            "user_prompt": user_prompt,
            "doc_type": doc_type,
            "style": self.style,
            "quality_threshold": threshold,
            "iterations": [],
            "final_image": None,
            "final_score": 0.0,
            "success": False,
            "early_stop": False,
            "early_stop_reason": None,
        }

        is_editing = input_image is not None

        # Create multi-turn chat session — model retains context across iterations.
        # Style directives live in system_instruction, not in the user prompt.
        config = self._build_config()
        chat = self.client.chats.create(model=self.image_model, config=config)

        # Build initial message
        if is_editing:
            with open(input_image, "rb") as f:
                source_bytes = f.read()
            source_mime = get_mime_type(input_image)
            initial_message: Any = [
                (
                    f"EDITING MODE: Modify the provided diagram based on these instructions.\n"
                    f"Keep all existing elements unless explicitly asked to remove them.\n\n"
                    f"USER EDIT REQUEST: {user_prompt}\n\n"
                    f"Generate the updated diagram maintaining publication quality."
                ),
                types.Part.from_bytes(data=source_bytes, mime_type=source_mime),
            ]
        else:
            initial_message = (
                f"USER REQUEST: {user_prompt}\n\n"
                f"Generate a publication-quality diagram."
            )

        print(f"\n{'='*60}")
        print(f"Nano Banana - {'Editing' if is_editing else 'Generating'} Diagram")
        print(f"{'='*60}")
        if is_editing:
            print(f"Source: {input_image}")
            print(f"Edit: {user_prompt}")
        else:
            print(f"Description: {user_prompt}")
        print(f"Model: {self.image_model}")
        print(f"Style: {self.style}")
        print(f"Document Type: {doc_type}")
        print(f"Quality Threshold: {threshold}/10")
        print(f"Max Iterations: {iterations}")
        print(f"Timeout: {self.timeout}s")
        print(f"Output: {output_path}")
        print(f"{'='*60}\n")

        total_start = time.time()
        score = 0.0
        critique = ""

        for i in range(1, iterations + 1):
            print(f"\n[Iteration {i}/{iterations}]")
            print("-" * 40)

            action = 'Editing' if is_editing and i == 1 else 'Generating'
            print(f"{action} diagram...")
            t_gen = time.time()

            try:
                if i == 1:
                    response = chat.send_message(initial_message)
                else:
                    # Send critique into the same chat — model has context of its prior output
                    refinement_msg = (
                        f"ITERATION {i}: The previous diagram scored {score}/10 "
                        f"(threshold: {threshold}/10). Address these improvements:\n"
                        f"{critique}\n\n"
                        f"Generate an improved version that fixes all issues while "
                        f"maintaining technical accuracy."
                    )
                    response = chat.send_message(refinement_msg)

                image_data = self._extract_image(response)
            except Exception as e:
                self._last_error = str(e)
                image_data = None

            gen_elapsed = time.time() - t_gen

            if not image_data:
                error_msg = self._last_error or "No image data in API response"
                print(f"Generation failed: {error_msg} (after {gen_elapsed:.1f}s)")
                results["iterations"].append({
                    "iteration": i,
                    "success": False,
                    "error": error_msg,
                })
                continue

            self._log(f"Generated image ({len(image_data)} bytes)")

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
                "critique": critique,
                "score": score,
                "needs_improvement": needs_improvement,
                "success": True,
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
            print("Sending critique for context-aware refinement...")

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
  python generate_diagram.py "Microservices architecture" -o arch.png --doc-type architecture

  # Visual abstract with dark background and glow
  python generate_diagram.py "API gateway as routing prism" -o visual.png --style visual-abstract --doc-type journal

  # Wide diagram with aspect ratio
  python generate_diagram.py "System overview" -o system.png --aspect-ratio 16:9 --resolution 2K

  # Minimal style
  python generate_diagram.py "Simple flowchart" -o flow.png --style minimal

Style Presets:
  technical        White background, accessible, standard diagrams (default)
  visual-abstract  Dark background, glow effects, Nature-quality figures
  minimal          White background, thin lines, no decoration

Document Types (quality thresholds):
  specification 8.5/10    journal       8.5/10
  architecture  8.0/10    conference    8.0/10
  proposal      8.0/10    thesis        8.0/10
  grant         8.0/10    sprint        7.5/10
  report        7.5/10    preprint      7.5/10
  readme        7.0/10    poster        7.0/10
  presentation  6.5/10    default       7.5/10

Model:
  Diagrams use Nano Banana Pro (gemini-3-pro-image-preview) for highest quality.
  Quality review uses Gemini 3.1 Pro (gemini-3.1-pro-preview).

Resolutions:
  512, 1K, 2K, 4K

Environment:
  GEMINI_API_KEY        Google Gemini API key (free tier at aistudio.google.com)
        """
    )

    parser.add_argument("prompt", help="Description of the diagram to generate")
    parser.add_argument("-o", "--output", required=True,
                       help="Output image path (e.g., diagram.png)")
    parser.add_argument("--style", default=DEFAULT_STYLE,
                       choices=sorted(STYLE_PRESETS.keys()),
                       help=f"Style preset (default: {DEFAULT_STYLE})")
    parser.add_argument("--iterations", type=int, default=2,
                       help="Maximum refinement iterations (default: 2, max: 2)")
    parser.add_argument("--doc-type", default="default",
                       choices=list(NanoBananaGenerator.QUALITY_THRESHOLDS.keys()),
                       help="Document type for quality threshold (default: default)")
    parser.add_argument("--input", "-i", type=str,
                       help="Input diagram image to edit (enables edit mode)")
    parser.add_argument("--aspect-ratio", type=str,
                       choices=["1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1",
                                "4:3", "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"],
                       help="Image aspect ratio (e.g. 16:9, 1:1, 4:3)")
    parser.add_argument("--resolution", type=str,
                       choices=["512", "1K", "2K", "4K"],
                       help="Image resolution (512, 1K, 2K, 4K)")
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
            api_key=args.api_key,
            verbose=args.verbose,
            timeout=args.timeout,
            resolution=args.resolution,
            aspect_ratio=args.aspect_ratio,
            style=args.style,
        )
        results = generator.generate_iterative(
            user_prompt=args.prompt,
            output_path=args.output,
            iterations=args.iterations,
            doc_type=args.doc_type,
            input_image=args.input,
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
