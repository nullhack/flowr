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

- **Background/flour:** `#faf8f3` → `#f0ebe3` — flour white, the canvas for state diagrams
- **Primary text:** `#3d2b1f` → `#2a1a10` — dark bran, the grain that carries weight
- **Accent/crust:** `#c49a3c` → `#daa840` — golden crust, used for borders, arrows, structural lines — never body text
- **Secondary/malt:** `#6b8f71` → `#4a7a50` — malt green, for states, labels, secondary hierarchy
- **Stone/bran:** `#e8e2d8` → `#c4baa8` — the structural colour; table borders, diagram dividers
- **Logo:** `docs/assets/logo.svg`
- **Banner:** `docs/assets/banner.svg`

> Dark bran `#2a1a10` on flour `#faf8f3` achieves >12:1 contrast (WCAG AAA). Crust gold is decorative; it never carries meaning that must be read.

### Logo

A grain-to-graph mark — a single wheat grain at top (organic, rounded) that transforms into three branching paths below (geometric, directional), ending in open circles representing states. The grain IS the graph: the raw material becomes structure. Dark bran `#3d2b1f` for paths, grain outline, and seed line; crust gold `#c49a3c` for grain fill. Transparent background.

### Banner

Flour `#faf8f3` background. Centred `flowr` wordmark in a clean sans-serif with letter-spacing — `flow` in dark bran `#2a1a10`, `r` in crust gold `#c49a3c`. A thin crust-gold rule below the title. No logo mark, no subtitle, no vertical divider.

## Release Naming

- **Convention:** `adjective-grain`
- **Theme:** Grains and flour — the raw material that becomes structure through craft. Every release name is a grain or flour term paired with an adjective that evokes the release's character (e.g. "Hardy Spelt", "Refined Semolina", "Whole Rye").
- **Rationale:** flowr comes from flour — the raw ingredient that, through kneading (specification, validation, shaping), becomes structured bread (a working workflow). Grains are the oldest engineered material: selected, ground, sifted, leavened, baked. Each release shapes the raw material further. The grain in each release name is a statement about craft and transformation.
- **Excluded words:** *(none)*

## Wording

Every word carries weight. Kneading is deliberate work — no shortcuts, no waste.

- **Avoid:** `easy`, `simple`, `just`, `quick`, `boilerplate`, `scaffold`, `magic`, `automagically`
- **Prefer:** `precise`, `unambiguous`, `validated`, `structured`, `specification-grade`, `knead`