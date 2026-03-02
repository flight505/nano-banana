---
name: kroki
description: "Render text-based diagrams (Mermaid, PlantUML, GraphViz, D2, and 23 more) to PNG/SVG via Kroki.io. Use ONLY when the user explicitly asks for text-based diagram rendering or a specific diagram language."
allowed-tools: [Read, Write, Edit, Bash]
disable-model-invocation: true
---

# Nano Banana - Kroki Diagram Rendering

## Overview

Render text-based diagrams to PNG, SVG, PDF, or JPEG using [Kroki.io](https://kroki.io). Supports 27 diagram languages including Mermaid, PlantUML, GraphViz, D2, Excalidraw, and more.

**Key Features:**
- 27 diagram languages in one tool
- PNG, SVG, PDF, JPEG output
- Zero dependencies (Python stdlib only)
- Free, open-source rendering service
- Reads from file, inline text, or stdin

## When to Use This Skill

Use this skill **only** when the user explicitly asks for:

- Rendering a text-based diagram to an image file (PNG/SVG)
- A specific diagram language (PlantUML, GraphViz/DOT, D2, etc.)
- Converting diagram source code to a visual image

**Do NOT use this skill when:**
- The user just wants Mermaid in a markdown file (Claude generates this natively)
- The user wants an AI-generated diagram from a description (use the `diagram` skill instead)
- The user wants a creative image (use the `image` skill instead)

## Quick Start

```bash
# Render Mermaid to PNG
python3 skills/kroki/scripts/render_diagram.py -t mermaid -o flowchart.png --source '
flowchart LR
    A[User] --> B[API Gateway]
    B --> C[Auth Service]
    B --> D[Order Service]
    C --> E[(Database)]
    D --> E
'

# Render PlantUML sequence diagram
python3 skills/kroki/scripts/render_diagram.py -t plantuml -o sequence.svg --source '
@startuml
Alice -> Bob: Authentication Request
Bob --> Alice: Authentication Response
Alice -> Bob: Another request
@enduml
'

# Render from a file
python3 skills/kroki/scripts/render_diagram.py -t graphviz -i architecture.dot -o architecture.png

# Render D2 diagram
python3 skills/kroki/scripts/render_diagram.py -t d2 -o system.svg --source '
server: Web Server
database: PostgreSQL
cache: Redis

server -> database: queries
server -> cache: reads
'

# List all 27 supported types
python3 skills/kroki/scripts/render_diagram.py --list-types
```

## Supported Diagram Types

| Type | ID | Best For |
|------|-----|----------|
| **Mermaid** | `mermaid` | Flowcharts, sequence, class, ERD, Gantt |
| **PlantUML** | `plantuml` | UML diagrams, sequence, activity, class |
| **GraphViz** | `graphviz` | Directed/undirected graphs (DOT language) |
| **D2** | `d2` | Modern declarative diagrams |
| **C4 PlantUML** | `c4plantuml` | C4 software architecture model |
| **Structurizr** | `structurizr` | C4 architecture DSL |
| **Excalidraw** | `excalidraw` | Hand-drawn style (JSON, SVG only) |
| **ERD** | `erd` | Entity-relationship diagrams |
| **DBML** | `dbml` | Database schema markup |
| **BPMN** | `bpmn` | Business process diagrams (SVG only) |
| **BlockDiag** | `blockdiag` | Block diagrams |
| **NwDiag** | `nwdiag` | Network diagrams |
| **SeqDiag** | `seqdiag` | Sequence diagrams |
| **ActDiag** | `actdiag` | Activity diagrams |
| **Ditaa** | `ditaa` | ASCII art → diagram |
| **Svgbob** | `svgbob` | ASCII art → SVG |
| **Nomnoml** | `nomnoml` | UML-like text diagrams (SVG only) |
| **Pikchr** | `pikchr` | PIC-like diagram markup |
| **Bytefield** | `bytefield` | Protocol/byte field diagrams |
| **Vega** | `vega` | Data visualization (JSON) |
| **Vega-Lite** | `vegalite` | Simplified Vega (JSON) |
| **WaveDrom** | `wavedrom` | Digital timing diagrams (JSON) |
| **WireViz** | `wireviz` | Wiring harness diagrams (YAML) |
| **PacketDiag** | `packetdiag` | Packet header diagrams |
| **RackDiag** | `rackdiag` | Server rack diagrams |
| **Symbolator** | `symbolator` | HDL symbol diagrams |
| **UMlet** | `umlet` | UML diagrams (XML) |

## Output Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| PNG | `.png` | Default, works for all types |
| SVG | `.svg` | Vector, scalable, best for web |
| PDF | `.pdf` | Best for print/documents |
| JPEG | `.jpeg` | Lossy, smaller file size |

Some types (bpmn, excalidraw, nomnoml, svgbob) only support SVG — the script auto-switches.

## Input Methods

```bash
# From file
python3 render_diagram.py -t mermaid -i diagram.mmd -o output.png

# Inline source
python3 render_diagram.py -t graphviz -o graph.png --source 'digraph G {A->B->C}'

# From stdin (pipe)
cat diagram.puml | python3 render_diagram.py -t plantuml -o output.svg
```

## Self-Hosted Server

Use `--server` to point to a self-hosted Kroki instance:

```bash
python3 render_diagram.py -t mermaid -i flow.mmd -o flow.png --server http://localhost:8000
```

## Python API

```python
from skills.kroki.scripts.render_diagram import render_diagram

# Render Mermaid to PNG
render_diagram(
    source="flowchart LR\n  A-->B-->C",
    diagram_type="mermaid",
    output_path="flow.png"
)

# Render PlantUML to SVG
render_diagram(
    source="@startuml\nA -> B: hello\n@enduml",
    diagram_type="plantuml",
    output_path="seq.svg"
)
```

## Comparison: kroki vs diagram Skills

| Aspect | `kroki` Skill | `diagram` Skill |
|--------|--------------|-----------------|
| **Input** | Text source code (Mermaid, DOT, etc.) | Natural language description |
| **Rendering** | Kroki.io API (deterministic) | Gemini AI (creative, non-deterministic) |
| **Quality Review** | No (text renders exactly) | Yes (AI reviews output) |
| **Version Control** | Source text is git-friendly | Generated images only |
| **Best For** | Exact diagrams from code | Diagrams from descriptions |
| **Cost** | Free (kroki.io) | API costs (Gemini) |

**Rule of thumb**: If you have the diagram source code → use `kroki`. If you have a description and want AI to create it → use `diagram`.

## Troubleshooting

### "Kroki API error (400)"
Your diagram source has a syntax error. Check the syntax for your diagram type.

### "Connection error"
Kroki.io may be temporarily unavailable. Try again, or use `--server` with a self-hosted instance.

### SVG-only types
Some types (bpmn, excalidraw, nomnoml, svgbob) only support SVG output. The script auto-switches to SVG if you request PNG for these types.
