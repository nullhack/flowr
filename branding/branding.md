# Branding — flowr

> *Non-deterministic state machine specification to knead workflows.*

Agents read this file before generating release names, C4 diagrams, README banners, or any document with visual or copy identity. All fields are optional; absent or blank fields fall back to defaults (adjective-grain release names, Mermaid default colours, no wording constraints).

**Ownership**: The stakeholder owns this file. The design agent proposes changes (colour palettes, visual assets, wording updates); the stakeholder approves them. No other agent edits this file.

---

## Identity

- **Project name:** flowr
- **Tagline:** Non-deterministic state machine specification to knead workflows.
- **Mission:** Give engineers a precise, unambiguous format for defining workflow state machines — and the tools to validate, query, and visualise them.
- **Vision:** The standard format for non-deterministic state machine workflows, wherever workflows need defining.
- **Tone of voice:** Precise, grounded, unambiguous. The craft metaphor is in the name; the product is engineering-grade specification. No hand-waving.

## Visual

The palette is drawn from flour, wheat, and crust — the transformation from raw grain to structured form. Every colour choice serves legibility first; decoration is secondary.

- **Background/flour:** `#ffffff` → `#f8fafc` — clean white, the canvas for state diagrams
- **Primary text:** `#0f172a` → `#475569` — slate dark, the grain that carries weight
- **Accent/crust:** `#3b82f6` → `#60a5fa` — blue accent, used for borders, arrows, structural lines — never body text
- **Secondary/malt:** `#10b981` — emerald green, for states, labels, secondary hierarchy
- **Stone/bran:** `#e2e8f0` → `#f1f5f9` — the structural colour; table borders, diagram dividers
- **Supplementary:** `#8b5cf6` (purple), `#14b8a6` (teal), `#f59e0b` (amber), `#ef4444` (danger)
- **Logo:** `docs/assets/logo.svg`
- **Banner:** `docs/assets/banner.svg`

> Slate `#0f172a` on white `#ffffff` achieves >18:1 contrast (WCAG AAA). Blue accent is decorative; it never carries meaning that must be read.

### Logo

A seed-to-graph mark — a filled blue circle at top (the seed, the initial state) that branches into three curved paths below, ending in open circles representing reachable states. The seed IS the graph: the raw material becomes structure. Slate `#0f172a` for paths and outlines; blue accent `#3b82f6` for the seed fill. Transparent background.

### Banner

White `#ffffff` background. Centred `flowr` wordmark in a clean sans-serif with letter-spacing — `flow` in slate `#0f172a`, `r` in blue accent `#3b82f6`. A thin blue-accent rule below the title. No logo mark, no subtitle, no vertical divider.

## Release Naming

- **Convention:** `adjective-grain`
- **Theme:** Grains and flour — the raw material that becomes structure through craft. Every release name is a grain or flour term paired with an adjective that evokes the release's character (e.g. "Hardy Spelt", "Refined Semolina", "Whole Rye").
- **Rationale:** flowr comes from flour — the raw ingredient that, through kneading (specification, validation, shaping), becomes structured bread (a working workflow). Grains are the oldest engineered material: selected, ground, sifted, leavened, baked. Each release shapes the raw material further. The grain in each release name is a statement about craft and transformation.
- **Excluded words:** *(none)*

## Wording

Every word carries weight. Kneading is deliberate work — no shortcuts, no waste.

- **Avoid:** `easy`, `simple`, `just`, `quick`, `boilerplate`, `scaffold`, `magic`, `automagically`
- **Prefer:** `precise`, `unambiguous`, `validated`, `structured`, `specification-grade`, `knead`