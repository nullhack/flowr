# Product Definition: flowr

> **Status:** BASELINED (2026-04-22)
> v1 scope delivered. See `docs/features/completed/` for accepted .feature files.
> This document is the single source of truth for project scope and conventions.

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
- **Tool Authors** — build editors, visualizers, or other tooling on top of the specification and validator
- Both humans and machines write and validate flows; the CLI is human-facing, the library is machine-facing

## Quality Attributes

| Attribute | Scenario | Target | Priority |
|-----------|----------|--------|----------|
| Correctness | When a flow definition is validated, all MUST violations are reported | Zero false negatives on MUST rules | Must |
| Usability | When a developer runs a CLI subcommand, the output is unambiguous and actionable | Key-value text format with clear error messages | Must |
| Extensibility | When a new condition operator is added, only the condition module changes | Single-module change for new operators | Should |
| Performance | When a developer validates a flow with up to 100 states, the result returns in under 1 second | < 1s for 100-state flow | Should |

---

## Out of Scope

- Runtime engine or session tracking
- JSON Schema deliverable
- Image rendering (Mermaid text only; `image` subcommand deferred)
- Auto-rollback or transition attempt limits
- Parallel/fork-join states
- Action execution
- Transition count tracking

## Delivery Order

1 → 2 (CLI depends on domain model)

---

## Project Conventions

### Definition of Done

All criteria must be met before a feature is considered done.

**Development:**

- [ ] All BDD scenarios from the .feature file pass
- [ ] Quality Gate passes all three tiers (Design → Structure → Conventions)
- [ ] Test coverage meets project threshold (≥ 80%)
- [ ] No test coupling — tests verify behavior, not structure
- [ ] Production code follows priority order: YAGNI > DRY > KISS > OC > SOLID > Design Patterns
- [ ] Code uses ubiquitous language from glossary.md

**Review:**

- [ ] CI pipeline passes all three tiers (Design → Structure → Conventions)
- [ ] Code Review approved by R (independent reviewer, not the SE who wrote the code)
- [ ] Acceptance Testing passed — PO verifies BDD scenarios behave as expected

**Deployment:**

- [ ] Release Verification checklist completed
- [ ] CHANGELOG.md updated

### Deployment

**Deployment type:** CLI / Library

#### Common (all deployment types)

- [ ] Version bumped in pyproject.toml
- [ ] CHANGELOG.md updated with version and delivered scenarios
- [ ] Git tag created (format: `v<semver>`)

#### CLI / Library

- [ ] Package builds without errors (`python -m build`)
- [ ] Package published to PyPI (`twine upload dist/*`)
- [ ] Installable from PyPI in clean environment

#### Rollback Plan

Revert the git tag and publish a patch version with the fix.

### Branch Strategy

- **Convention:** Trunk-based (short-lived feature branches from trunk, PR before merge)
- **Branch naming:** `<type>/<stem>` (e.g., `feature/cli-entrypoint`, `fix/validate-cycle`)
- **Merge policy:** Squash merge to trunk after approval

---

## Scope Changes

| Date | Session | Change | Reason |
|------|---------|--------|--------|
| 2026-04-22 | Session 1 | Initial product definition created | Discovery |
| 2026-04-26 | Session 2 | Refined scope from "Python project template" to "flow specification format" | Pivot based on stakeholder input |