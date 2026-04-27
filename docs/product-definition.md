# Product Definition: flowr

> **Status: APPROVED**
> v1 scope delivered. See `docs/features/completed/` for accepted .feature files.

---

## What flowr IS

- A **YAML specification** for non-deterministic state machine workflows
- A **Python validator** that checks flow definitions against the specification
- A **CLI** that validates, queries, and converts flow definitions from the terminal
- A **Mermaid converter** that generates state diagrams from flow definitions
- **Enforces valid transitions** — lists available next steps AND rejects invalid ones
- **Verifies guard conditions** at transition time using simple expressions (`==`, `!=`, `>=`, `<=`, `>`, `<`, `~=`) against closed evidence schemas
- **Validates structural constraints** — missing fields, ambiguous targets, cross-flow cycles, subflow exit contracts

## What flowr IS NOT

- Does NOT execute actions or side effects
- Does NOT track session state (stateless — each command is a one-shot invocation)
- Does NOT modify flow definitions (flows are immutable once loaded)
- Does NOT provide a runtime engine or session manager
- Does NOT generate JSON Schema (internal representation uses Python dataclasses; JSON is for CLI output only)
- Does NOT render images directly (Mermaid text output only; image rendering deferred to v2)

## Why does this exist

No existing YAML standard covers non-deterministic state machine workflows with per-state agent assignment and filesystem-as-source-of-truth. Existing solutions (XState, SCXML, Serverless Workflow, BPMN) target execution engines or deterministic workflows. flowr fills this gap: a declarative, validatable, toolable format for workflows that branch on evidence rather than control flow.

## Users

- **Developers** — write and validate flow YAML files, integrate the Python library into tooling
- **Tool authors** — build editors, visualizers, or other tooling on top of the specification and validator
- Both humans and machines write and validate flows; the CLI is human-facing, the library is machine-facing

## Out of Scope for v1

- Runtime engine or session tracking
- JSON Schema deliverable
- Image rendering (Mermaid text only; `image` subcommand deferred)
- Auto-rollback or transition attempt limits
- Parallel/fork-join states
- Action execution
- Transition count tracking

## Delivery Order

1 → 2 (CLI depends on domain model)