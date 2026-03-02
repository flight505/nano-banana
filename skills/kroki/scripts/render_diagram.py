#!/usr/bin/env python3
"""
Render text-based diagrams to PNG/SVG using Kroki.io.

Supports 27 diagram types including Mermaid, PlantUML, GraphViz, D2,
Excalidraw, BPMN, and more. Zero dependencies (Python stdlib only).

Usage:
    # Render a Mermaid diagram from a file
    python render_diagram.py -t mermaid -i diagram.mmd -o diagram.png

    # Render PlantUML from stdin
    echo '@startuml\nA -> B\n@enduml' | python render_diagram.py -t plantuml -o seq.svg

    # Render inline GraphViz
    python render_diagram.py -t graphviz -o graph.png --source 'digraph G {A->B}'

    # List all supported diagram types
    python render_diagram.py --list-types
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import socket
import time
from pathlib import Path
from typing import Optional

KROKI_BASE_URL = "https://kroki.io"

DIAGRAM_TYPES = {
    # Core / most popular
    "mermaid": "Mermaid — flowcharts, sequence, class, ERD, Gantt, etc.",
    "plantuml": "PlantUML — UML diagrams, sequence, activity, class, etc.",
    "graphviz": "Graphviz (DOT) — directed/undirected graphs",
    "d2": "D2 — modern declarative diagramming language",
    "c4plantuml": "C4 via PlantUML — software architecture (C4 model)",
    "structurizr": "Structurizr — C4 architecture DSL",
    "excalidraw": "Excalidraw — hand-drawn style diagrams (JSON input)",
    # Data & databases
    "erd": "ERD — entity-relationship diagrams",
    "dbml": "DBML — database markup language",
    # Process & business
    "bpmn": "BPMN — business process diagrams (SVG only)",
    "actdiag": "ActDiag — activity diagrams",
    "seqdiag": "SeqDiag — sequence diagrams",
    # Network & infrastructure
    "nwdiag": "NwDiag — network diagrams",
    "packetdiag": "PacketDiag — packet header diagrams",
    "rackdiag": "RackDiag — rack diagrams",
    # Block & box diagrams
    "blockdiag": "BlockDiag — block diagrams",
    "ditaa": "Ditaa — ASCII art to diagram",
    "svgbob": "Svgbob — ASCII art to SVG",
    "nomnoml": "Nomnoml — UML-like text diagrams",
    "pikchr": "Pikchr — PIC-like diagram markup",
    # Specialized
    "bytefield": "Bytefield — byte field / protocol diagrams",
    "symbolator": "Symbolator — HDL symbol diagrams",
    "umlet": "UMlet — UML diagrams (XML input)",
    "vega": "Vega — data visualization grammar (JSON)",
    "vegalite": "Vega-Lite — simplified Vega (JSON)",
    "wavedrom": "WaveDrom — digital timing diagrams (JSON)",
    "wireviz": "WireViz — wiring harness diagrams (YAML)",
}

# Output formats known to work for most types
OUTPUT_FORMATS = ["png", "svg", "pdf", "jpeg"]

# Some types only support SVG
SVG_ONLY_TYPES = {"bpmn", "excalidraw", "nomnoml", "svgbob"}


def render_diagram(
    source: str,
    diagram_type: str,
    output_path: str,
    output_format: Optional[str] = None,
    base_url: str = KROKI_BASE_URL,
    timeout: int = 30,
) -> str:
    """Render a text-based diagram to an image file via Kroki.io.

    Args:
        source: Diagram source text (Mermaid, PlantUML, DOT, etc.)
        diagram_type: Kroki diagram type identifier (e.g. "mermaid", "plantuml")
        output_path: Path to save the rendered image
        output_format: Output format (png, svg, pdf, jpeg). Auto-detected from extension.
        base_url: Kroki server URL (default: https://kroki.io)
        timeout: Request timeout in seconds (default: 30)

    Returns:
        The output file path.

    Raises:
        ValueError: If diagram type is unsupported or source is empty.
        RuntimeError: On API errors or timeouts.
    """
    diagram_type = diagram_type.lower().strip()
    if diagram_type not in DIAGRAM_TYPES:
        raise ValueError(
            f"Unsupported diagram type: '{diagram_type}'\n"
            f"Run with --list-types to see all {len(DIAGRAM_TYPES)} supported types."
        )

    if not source or not source.strip():
        raise ValueError("Diagram source is empty")

    # Auto-detect output format from file extension
    if not output_format:
        ext = Path(output_path).suffix.lower().lstrip(".")
        output_format = ext if ext in OUTPUT_FORMATS else "png"

    # Enforce SVG-only types
    if diagram_type in SVG_ONLY_TYPES and output_format != "svg":
        print(f"Note: {diagram_type} only supports SVG output. Switching to SVG.")
        output_format = "svg"
        if not output_path.lower().endswith(".svg"):
            output_path = str(Path(output_path).with_suffix(".svg"))

    # Build POST request with JSON body
    url = f"{base_url}/{diagram_type}/{output_format}"
    payload = json.dumps({
        "diagram_source": source,
        "diagram_type": diagram_type,
        "output_format": output_format,
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "NanoBanana/2.0 (https://github.com/flight505/nano-banana)",
        },
        method="POST"
    )

    t_start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            image_data = response.read()
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t_start
        error_body = ""
        try:
            error_body = e.read().decode("utf-8", errors="replace")[:500]
        except Exception:
            error_body = str(e)
        raise RuntimeError(
            f"Kroki API error ({e.code}): {error_body} (after {elapsed:.1f}s)"
        )
    except urllib.error.URLError as e:
        elapsed = time.time() - t_start
        if isinstance(e.reason, socket.timeout):
            raise RuntimeError(f"Kroki request timed out after {timeout}s")
        raise RuntimeError(f"Connection error: {e.reason} (after {elapsed:.1f}s)")
    except socket.timeout:
        raise RuntimeError(f"Kroki request timed out after {timeout}s")

    elapsed = time.time() - t_start

    # Save output
    output_dir = Path(output_path).parent
    if output_dir and not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(image_data)

    size_kb = len(image_data) / 1024
    print(f"Rendered {diagram_type} → {output_path} ({size_kb:.1f} KB, {elapsed:.1f}s)")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Render text-based diagrams to PNG/SVG via Kroki.io",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Render Mermaid from file
  python render_diagram.py -t mermaid -i flowchart.mmd -o flowchart.png

  # Render PlantUML inline
  python render_diagram.py -t plantuml -o seq.svg --source '@startuml
  Alice -> Bob: Hello
  @enduml'

  # Render GraphViz DOT
  python render_diagram.py -t graphviz -i graph.dot -o graph.png

  # Render D2 diagram
  python render_diagram.py -t d2 -i arch.d2 -o arch.svg

  # Read from stdin
  cat diagram.mmd | python render_diagram.py -t mermaid -o output.png

  # List all supported types
  python render_diagram.py --list-types

  # Use a self-hosted Kroki server
  python render_diagram.py -t mermaid -i flow.mmd -o flow.png --server http://localhost:8000

Supported output formats:
  png (default), svg, pdf, jpeg
  Note: some diagram types (bpmn, excalidraw, nomnoml, svgbob) only support SVG.

Diagram source:
  Provide diagram text via --input FILE, --source STRING, or stdin (pipe).
        """
    )

    parser.add_argument("-t", "--type", required="--list-types" not in sys.argv,
                       choices=sorted(DIAGRAM_TYPES.keys()),
                       help="Diagram type (e.g. mermaid, plantuml, graphviz, d2)")
    parser.add_argument("-i", "--input", type=str,
                       help="Input file containing diagram source")
    parser.add_argument("-o", "--output", type=str, default="diagram.png",
                       help="Output file path (default: diagram.png)")
    parser.add_argument("--source", type=str,
                       help="Inline diagram source text")
    parser.add_argument("--format", type=str,
                       choices=OUTPUT_FORMATS,
                       help="Output format (auto-detected from extension if omitted)")
    parser.add_argument("--server", type=str, default=KROKI_BASE_URL,
                       help=f"Kroki server URL (default: {KROKI_BASE_URL})")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Request timeout in seconds (default: 30)")
    parser.add_argument("--list-types", action="store_true",
                       help="List all supported diagram types and exit")

    args = parser.parse_args()

    if args.list_types:
        print(f"Supported diagram types ({len(DIAGRAM_TYPES)}):\n")
        max_name = max(len(k) for k in DIAGRAM_TYPES)
        for name, desc in sorted(DIAGRAM_TYPES.items()):
            svg_note = " [SVG only]" if name in SVG_ONLY_TYPES else ""
            print(f"  {name:<{max_name}}  {desc}{svg_note}")
        print(f"\nUsage: python render_diagram.py -t <type> -i <file> -o output.png")
        sys.exit(0)

    # Read diagram source: --source > --input > stdin
    source = None
    if args.source:
        source = args.source
    elif args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}")
            sys.exit(1)
        source = input_path.read_text(encoding="utf-8")
    elif not sys.stdin.isatty():
        source = sys.stdin.read()
    else:
        print("Error: No diagram source provided.")
        print("Use --input FILE, --source STRING, or pipe via stdin.")
        sys.exit(1)

    try:
        render_diagram(
            source=source,
            diagram_type=args.type,
            output_path=args.output,
            output_format=args.format,
            base_url=args.server,
            timeout=args.timeout,
        )
    except (ValueError, RuntimeError) as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
