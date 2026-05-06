# PM_20260506_duplicate-docs-tree: Orchestrator created duplicate documentation tree instead of updating existing project-level documents

## Failed At

scope-boundary (discovery-flow) — Orchestrator dispatched PO subagent with instructions to create `docs/features/export/product_definition.md`, fabricating a new directory tree (`docs/features/export/`) instead of updating the existing `docs/spec/product_definition.md`.

## Root Cause

The orchestrator assumed "feature = new document tree" without reading the existing artifact. The state's `out` lists `product_definition.md` — a bare filename appearing in both `in` and `out`. When the same artifact name appears in both lists, it means UPDATE the existing file, not CREATE a new one elsewhere. The orchestrator fabricated the path `docs/features/export/product_definition.md` without checking that `docs/spec/product_definition.md` already exists and already contains feature-specific sections for three previous features (cli-flow-name-resolution, session-management, remove-fuzzy-match-operator) appended to the project-level document.

## Missed Gate

The orchestrator skipped reading the existing `docs/spec/product_definition.md` before dispatch. AGENTS.md states: "Read inputs on demand, not eagerly. List directories first, read selectively." The `in` list included `product_definition.md` — the orchestrator should have listed the directory, found the existing file, read it to understand the established pattern (project-level doc with feature-specific sections appended), and instructed the subagent to UPDATE it. Instead, the orchestrator dispatched with fabricated output path and the subagent produced a standalone document that duplicated information already maintained elsewhere.

## Fix

Before dispatching to any subagent, when an artifact name appears in both `in` and `out`:

1. Read the existing artifact to determine whether the output is an update or a new creation.
2. If the artifact exists and follows an established pattern (e.g., project-level doc with feature-specific sections), instruct the subagent to UPDATE it — preserving existing sections and appending new feature-specific content.
3. Only CREATE a new artifact when the filename does not match any existing file in the project.

Rule: **Same name in `in` and `out` means UPDATE, not CREATE.** The orchestrator must verify this before constructing dispatch instructions.

## Restart Check

Before dispatching for any state with overlapping `in`/`out` artifact names, confirm the output path resolves to the existing file. If the orchestrator cannot locate the existing artifact, stop and flag rather than fabricating a new path.
