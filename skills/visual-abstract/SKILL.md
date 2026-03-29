---
name: visual-abstract
description: "Create Nature-quality visual abstracts — scientific figures using visual metaphors, isometric depth, and physical analogies to convey complex technical systems. Use for README hero images, paper figures, blog graphics, or when the user wants diagrams that go beyond boxes and arrows. Triggers on: 'visual abstract', 'scientific figure', 'Nature-quality', 'publication graphic', 'infographic', 'visual metaphor', or requests for rich/expressive/artistic diagrams."
allowed-tools: [Read, Write, Edit, Bash, Grep, Glob]
disable-model-invocation: false
---

# Nano Banana — Visual Abstract Generation

Create publication-quality scientific figures that use visual metaphors, physical analogies, and isometric depth to convey complex technical systems. These are the figures you see in Nature, Science, and Nature Methods — not boxes and arrows.

## Visual Abstracts vs Standard Diagrams

| | Standard diagram (`diagram` skill) | Visual abstract (this skill) |
|---|---|---|
| **Prompt style** | "API gateway connects to auth service" | "API gateway as a routing prism splitting request beams into wavelengths" |
| **Visual output** | Boxes, arrows, labels | Metaphors, depth, physical analogies, glow, transparency |
| **Audience** | Engineers reading architecture docs | Anyone — meaning is conveyed through visual metaphor |
| **Use case** | PRDs, architecture docs, ERDs | README heroes, paper figures, blog posts, talks |

Use the `diagram` skill for standard technical documentation. Use this skill when you want a human to *feel* the system, not just read it.

## When to Use

- README hero images that explain a project at a glance
- Paper figures for journals, conferences, preprints
- Blog post graphics that convey architecture to non-engineers
- Conference talk visuals
- Any request for "rich", "expressive", "artistic", or "Nature-quality" diagrams

## Quick Start

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/diagram/scripts/generate_diagram.py \
  "<your visual-abstract prompt>" \
  -o visual-abstract.png \
  --style visual-abstract \
  --doc-type journal \
  --resolution 2K
```

The `--style visual-abstract` sends dark-background, glow, and metaphor directives via `system_instruction` — separated from your content prompt. The `--doc-type journal` sets the quality threshold to 8.5/10. The generation engine iterates up to twice to meet this bar.

## The Metaphor Translation Process

This is the core skill. For every technical concept, ask: "What does this LOOK LIKE physically?"

### Step 1: Read the system

Explore the codebase or user description. Understand the architecture, data flow, and key abstractions. Use Read, Grep, and Glob to build a mental model.

### Step 2: Identify 3-5 key concepts

Pick the concepts that are most important to communicate. Not everything needs to be in the figure — pick the ones that tell the story.

### Step 3: Map each concept to a visual metaphor

Use the vocabulary table below, or invent a new metaphor. The principle: describe what the concept LOOKS LIKE physically, not what it IS abstractly.

**Bad:** "The data is compressed by the extraction module"
**Good:** "Raw data flows as a thick, chaotic bundle of luminous fibers through a COMPRESSION FUNNEL — a physical narrowing that strips away noise. Discarded particles scatter and dim. What emerges is a thin, refined stream."

### Step 4: Choose spatial layout

| Layout | Best for | Example |
|--------|----------|---------|
| **Isometric exploded view** | Layered systems (stack, pipeline) | recall architecture — hooks, pipeline, storage as vertical layers |
| **Circular lifecycle** | Cyclical processes | recall how-it-works — capture → store → recall → repeat |
| **Cross-section** | Internal structure | Database internals, compression pipeline |
| **Constellation/network** | Distributed systems | Microservices, mesh networks |
| **Flow/river** | Data pipelines | ETL, CI/CD, streaming |

### Step 5: Describe data flow

Not arrows. Describe the physical medium:
- **Luminous fibers** — individual data streams
- **Particle flow** — many small items moving together
- **Liquid/fluid** — continuous data streams merging and splitting
- **Light beams** — request routing, API calls
- **Electrical current** — signal transmission, event propagation

### Step 6: Add composition details

Colors, lighting, glow, depth, transparency. Add quantitative labels where meaningful (sizes, percentages, counts, durations).

### Step 7: Append the style suffix

Always end the prompt with:

> Style: Publication-quality scientific figure. Dark background (#0d1117). Isometric depth. Subtle glow effects on active elements. Clean sans-serif typography. No cartoon elements. Information density of a Nature figure.

## Metaphor Vocabulary

Reference table for translating technical concepts into visual metaphors:

| Concept | Visual metaphor | Why it works |
|---------|----------------|--------------|
| Data compression | Funnel filtering particles, narrowing pipe | Physical narrowing = intuitive reduction |
| Storage layers | Geological strata, sedimentary layers | Time-layered accumulation, depth = age |
| Temporal decay | Brightness gradient (new = bright, old = dim) | Natural aging, fading memory |
| Protection / safety | Shield, vault, capsule, force field | Physical barrier = data protection |
| Data flow | Luminous fibers, pipes, streams, rivers | Physical medium carrying information |
| Filtering / selection | Sieve, prism splitting light, membrane | Physical separation of wanted from unwanted |
| API gateway | Routing prism splitting request beams | Light splitting = request routing |
| Load balancer | Distribution manifold, river delta | Physical flow splitting evenly |
| Cache | Fast-access crystal buffer, mirror surface | Crystalline = fast, ordered retrieval |
| Database | Deep storage matrix, geological core, vault | Depth = persistence, permanence |
| Network nodes | Constellation of connected stars | Natural clustering, visible connections |
| Context window | Layered transparent workspace, fish tank | Bounded space with visible contents |
| Summarization | Crystallization of raw material | Refinement from chaos to structure |
| Error / failure | Cracks, fractures, heat signatures, red glow | Physical damage = system damage |
| Budget / quota | Depleting gauge, meter, sand timer | Physical resource being consumed |
| Async operation | Detached/floating element, thin tether | Physical independence, loose coupling |
| Sync operation | Rigid connection, locked coupling, rail | Physical constraint, forced sequencing |
| Encryption | Sealed container, opacity, lock mechanism | Hidden contents = encrypted data |
| Queue | Pipeline with items waiting, conveyor belt | Physical ordering, first-in-first-out |
| Webhook / event | Spark, signal flare, ripple on surface | Sudden trigger, propagation |

## Composition Rules

1. **Dark background** (#0d1117) — maximum contrast, enables glow effects
2. **Isometric perspective** — creates depth without vanishing-point complexity
3. **Information flows** clockwise or top-to-bottom
4. **Color semantics:**
   - Blue (#4a9eff) — active, primary, processing
   - Green (#4aef7a) — storage, success, growth
   - Amber (#ffb347) — recall, retrieval, attention
   - Orange (#ff6b35) — protection, warning, critical path
   - Red (#ff4444) — error, failure, danger
   - Cyan (#00d4aa) — data pipeline, transformation
   - Gray (#666) — dormant, inactive, deprecated
5. **Glow** on active/current elements, **dim** on dormant/old
6. **Labels integrated** into the visual — not floating text boxes
7. **Quantitative data** where meaningful (sizes, percentages, counts)
8. **No cartoon elements** — scientific illustration aesthetic
9. **Sans-serif typography** — Geist, Inter, or Helvetica style
10. **Version badge** in top-right corner when applicable

## Prompt Template

Use this structure for every visual abstract:

```
Create a publication-quality scientific figure. Title: '<title>'. Dark background (#0d1117).

<1-2 sentence system description — what the figure is about>

LAYOUT: <isometric exploded view | circular lifecycle | cross-section | constellation | flow>

<ELEMENT 1 — name> (<color tone>):
<Detailed visual metaphor description. What does it look like? How does it
behave? What physical phenomenon does it represent? Include quantitative
labels if meaningful.>

<ELEMENT 2 — name> (<color tone>):
<Same treatment.>

<ELEMENT N>:
<...>

<DATA FLOW description — how information moves between elements, described
as a physical medium>

BOTTOM: '<tagline or key specs>'

Style: Publication-quality scientific figure. Dark background (#0d1117).
Isometric depth. Subtle glow effects on active elements. Clean sans-serif
typography. No cartoon elements. Information density of a Nature figure.
```

## Examples

### Example 1: Memory System Lifecycle

**Diagram skill would say:**
```
Memory system with session capture, episodic storage, and context injection.
Stop hook captures data, SessionStart injects it.
```

**Visual abstract prompt:**
```
Create a publication-quality scientific figure. Title: 'recall v1.2.0 —
How It Works'. Dark background (#0d1117).

This figure shows the lifecycle of a memory system for an AI coding
assistant. Use rich visual metaphors — NOT boxes and arrows.

LAYOUT: Circular lifecycle flowing clockwise, isometric perspective with
depth. Three phases arranged as segments of a circle.

PHASE 1 — CAPTURE (top, blue #4a9eff tones):
Show a SESSION as a glowing terminal window that is closing/fading. From
it, streams of data flow outward like luminous particles through fiber
optic cables. These streams represent the raw transcript — show it as a
thick, chaotic bundle (3.4MB label). The bundle passes through a
COMPRESSION FUNNEL — a visual narrowing that strips away noise (show
discarded particles scattering away, dimming). What emerges is a thin,
refined stream (42KB label, 98.8% compression). This refined stream flows
into a HAIKU BRAIN — a small, elegant neural node that transforms the
stream into structured knowledge. Git commit icons as anchor points.

PHASE 2 — STORE (right side, green #4aef7a tones):
Show EPISODIC STORAGE as stacked layers of translucent markdown pages —
like geological strata. Newest layers on top are brighter. Older layers
dim with temporal decay. A SEMANTIC layer floats nearby as a crystalline
knowledge graph — currently dormant with a subtle pulsing glow. A WORKING
STATE capsule sits as a protected vault.

PHASE 3 — RECALL (bottom-left, warm amber #ffb347 tones):
A fresh terminal window lights up. From episodic storage, relevant memories
flow back as curated streams through a BUDGET GATE — a metered injection
point labeled '4K chars'. Inside the session, recalled memories integrate
into Claude's context window as layered translucent panels.

COMPACTION PROTECTION (center, orange #ff6b35):
A shield around the working state. When context compacts (depicted as a
crushing force), the shield preserves the working state while everything
else is swept away.

Style: Publication-quality scientific figure. Dark background. Isometric
depth. Subtle glow effects. No cartoon elements.
```

### Example 2: CI/CD Pipeline

**Diagram skill would say:**
```
CI/CD pipeline with GitHub Actions, build, test, and deploy stages.
```

**Visual abstract prompt:**
```
Create a publication-quality scientific figure. Title: 'Continuous Delivery
Pipeline'. Dark background (#0d1117).

LAYOUT: Horizontal flow, left to right, with industrial/manufacturing
aesthetic. The pipeline is a physical processing facility.

SOURCE (far left, blue #4a9eff):
Code commits arrive as luminous data packets flowing through fiber optic
cables from a REPOSITORY — depicted as a crystalline archive with branching
structures (git branches as physical tree branches with glowing tips).
Multiple developer nodes feed into the repository like tributaries.

BUILD STAGE (cyan #00d4aa):
A FORGE — an industrial smelting chamber where raw code is compiled. Show
heat signatures and transformation. Dependencies flow in as raw materials
from a PACKAGE REGISTRY (shelved containers). The output is a refined
artifact — a glowing compiled binary or container image.

TEST STAGE (amber #ffb347):
A QUALITY CHAMBER with inspection beams scanning the artifact from multiple
angles. Show test suites as parallel analysis beams — unit tests as fine
beams, integration tests as broad sweeps, e2e tests as full-spectrum scans.
Failed tests produce red fracture lines. A QUALITY GATE at the exit only
opens when all beams pass (green).

DEPLOY STAGE (green #4aef7a):
The artifact enters a DISTRIBUTION MANIFOLD that splits the deployment
stream into environment channels — staging (dim), production (bright).
Show canary deployment as a thin test stream alongside the main flow.
Production servers depicted as active processing nodes in a constellation.

Style: Publication-quality scientific figure. Dark background. Industrial
manufacturing aesthetic with digital overlay. Subtle glow. No cartoon
elements.
```

## Generation Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--doc-type journal` | **Use this** | 8.5/10 quality threshold — highest standard |
| `--resolution 2K` | 1K | Higher resolution for print/retina |
| `--input <path>` | — | Edit an existing visual abstract |
| `-v` | off | Verbose output (shows scores, critiques) |
| `--timeout 120` | 120s | Increase for very complex prompts |

## Editing Visual Abstracts

To modify an existing visual abstract:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/diagram/scripts/generate_diagram.py \
  "Add a monitoring layer showing real-time metrics as oscilloscope traces" \
  --input existing-abstract.png \
  -o existing-abstract-v2.png \
  --style visual-abstract \
  --doc-type journal
```

Or use the command: `/nano-banana:edit existing-abstract.png "Add monitoring traces"`

## Tips for Higher Scores

- **Keep text labels SHORT** — AI image models hallucinate spelling in longer text. Use 1-3 word labels.
- **Be spatially explicit** — "above", "below", "left of", "flowing into" are more effective than abstract relationships.
- **Include quantitative data** — sizes, percentages, counts add information density and credibility.
- **Specify glow/dim for every element** — don't leave visual states ambiguous.
- **More detail = better results** — the 9.5-scoring prompt was ~1500 words. Don't be brief.
- **Name the physical metaphor explicitly** — "a COMPRESSION FUNNEL" not just "compression."

## Gotchas

- **Always pass `--style visual-abstract`**: This sends dark-background and glow directives via `system_instruction`, cleanly separated from your content prompt. Without it, you get the default white-background technical style.
- **Spelling artifacts**: AI-generated text in images often has minor character substitutions (e.g., "3.4MB" may render as "S.4MB"). Keep labels short and essential. The reviewer catches severe cases.
- **Iteration 2 is key**: First iterations score 6-7.5 due to spelling/layout issues. The review-and-iterate loop typically pushes to 9+. Don't set `--iterations 1`.
- **Timeout**: Complex prompts with many elements may need `--timeout 180`.
