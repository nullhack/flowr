# Product Definition: flowr

> **Status:** BASELINED (2026-04-22)
> v1 scope delivered. See `docs/features/completed/` for accepted .feature files.
> This document is the single source of truth for project scope and conventions.

---

## What flowr IS

- A **YAML specification** for non-deterministic state machine workflows
- A **Python validator** that checks flow definitions against the specification
- A **CLI** that validates, queries, and converts flow definitions from the terminal
- A **CLI that resolves flow names to file paths** using configured paths (short names resolved from flows directory; file paths used directly)
- A **session manager** that tracks workflow state across CLI invocations (init, show, set-state, transition, list)
- A **Mermaid converter** that generates state diagrams from flow definitions
- **Enforces valid transitions** — lists available next steps AND rejects invalid ones
- **Verifies guard conditions** at transition time using simple expressions (`==`, `!=`, `>=`, `<=`, `>`, `<`, `~=`) against closed evidence schemas
- **Validates structural constraints** — missing fields, ambiguous targets, cross-flow cycles, subflow exit contracts

## What flowr IS NOT

- Does NOT execute actions or side effects
- Does NOT modify flow definitions (flows are immutable once loaded)
- Does NOT provide a runtime engine or session manager for external tools (flowr tracks its own sessions, but does not expose a session API for other tools)
- Does NOT generate JSON Schema (internal representation uses Python dataclasses; JSON is for CLI output only)
- Does NOT render images directly (Mermaid text output only; image rendering deferred to v2)

## Why does this exist

No existing YAML standard covers non-deterministic state machine workflows with per-state agent assignment and filesystem-as-source-of-truth. Existing solutions (XState, SCXML, Serverless Workflow, BPMN) target execution engines or deterministic workflows. flowr fills this gap: a declarative, validatable, toolable format for workflows that branch on evidence rather than control flow.

## Users

- **Developers** — write and validate flow YAML files, integrate the Python library into tooling
- **Tool Authors** — build editors, visualizers, or other tooling on top of the specification and validator
- **Agent Operators** — AI agents running flowr commands in automated workflows who need session state to persist across invocations
- Both humans and machines write and validate flows; the CLI is human-facing, the library is machine-facing

## Quality Attributes

| Attribute | Scenario | Target | Priority |
|-----------|----------|--------|----------|
| Correctness | When a flow definition is validated, all MUST violations are reported | Zero false negatives on MUST rules | Must |
| Usability | When a developer runs a CLI subcommand, the output is unambiguous and actionable | Key-value text format with clear error messages | Must |
| Reliability | When a session file is written, the write is atomic | Temp-file-then-rename for all session writes | Must |
| Usability | When a user passes a flow name or file path as a CLI argument, both resolve correctly | Flow names and file paths both work as CLI arguments | Must |
| Backward Compatibility | When a user runs a command without --session, the behaviour is identical to the current version | Commands without --session behave identically to pre-session version | Must |
| Usability | When a user runs a session command, the output is structured and parseable | Session commands provide clear output in YAML or JSON format | Should |
| Extensibility | When a new condition operator is added, only the condition module changes | Single-module change for new operators | Should |
| Performance | When a developer validates a flow with up to 100 states, the result returns in under 1 second | < 1s for 100-state flow | Should |

---

## Out of Scope

- Runtime engine or session tracking for external tools
- Concurrent session access (multiple processes writing the same session)
- Session listing/management beyond init/show/set-state/list
- JSON Schema deliverable
- Image rendering (Mermaid text only; `image` subcommand deferred)
- Auto-rollback or transition attempt limits
- Parallel/fork-join states
- Action execution
- Transition count tracking

## Delivery Order

1 → cli-flow-name-resolution (2 → session-management) (CLI depends on domain model; session management depends on flow name resolution)

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

### Feature-Specific Definition of Done: cli-flow-name-resolution

These gates supplement the general Definition of Done above. All must pass before this feature is considered complete.

**Design Correctness:**

- [ ] All 7 BDD scenarios pass (a1b2c3d4, e5f6g7h8, i9j0k1l2, m3n4o5p6, q7r8s9t0, u1v2w3x4, y5z6a7b8)
- [ ] Flow name resolution is CLI-layer only — no changes to library functions (`load_flow_from_file`, `resolve_subflows`)
- [ ] File paths passed as `flow_file` work identically to the pre-feature behaviour (backward compatible)
- [ ] `--flows-dir` global flag overrides `pyproject.toml` `flows_dir` for a single invocation
- [ ] When neither a file path nor a flow name resolves, the CLI prints a clear error message showing both the name and the configured `flows_dir`

**Structure:**

- [ ] No changes to domain modules (`flowr/flow.py`, `flowr/validate.py`, `flowr/resolve.py`)
- [ ] Resolution logic isolated in `cli/resolution.py` (or equivalent CLI-layer module)
- [ ] Test coverage for all resolution paths: file path (direct), flow name (no extension), flow name (with `.yaml`), `--flows-dir` override, and not-found error

**Conventions:**

- [ ] Ubiquitous language used consistently: "Flow Name Resolution" (not "flow lookup" or "name mapping"), `flows_dir` (not `flowsDir` or `flows-directory`)
- [ ] `ruff check` and `ruff format` pass with zero errors
- [ ] `mypy` type-checking passes with no new errors

### Feature-Specific Definition of Done: session-management (core)

These gates supplement the general Definition of Done above. All must pass before this feature is considered complete.

**Design Correctness:**

- [ ] All 8 BDD scenarios pass (a1b2c3d4, i9j0k1l2, m3n4o5p6, u1v2w3x4, c9d0e1f2, o1p2q3r4, s5t6u7v8, w9x0y1z2)
- [ ] Session init creates a session at the flow's initial state; fails if a session already exists
- [ ] Session show displays flow, state, stack, and timestamps; displays subflow stack entries
- [ ] Session set-state updates the current state and persists it
- [ ] Session-aware transition auto-updates the session after mutation; pushes stack on subflow entry; pops stack on subflow exit
- [ ] Commands without `--session` behave identically to the current version (backward compatible)
- [ ] Session persistence uses atomic writes (temp-file-then-rename)
- [ ] `session init` does NOT accept params

**Structure:**

- [ ] Domain layer (`Session`, `SessionStackFrame` dataclasses) unchanged from existing implementation
- [ ] `SessionStore` Protocol and `YamlSessionStore` in infrastructure layer
- [ ] Session subcommands in `cli/session_cmd.py`
- [ ] `--session` flag on `transition` only (`next` and `check` are in the extended feature)
- [ ] Test coverage for all session operations including error paths

**Conventions:**

- [ ] Ubiquitous language used consistently: Session, Session Store, Session-Aware, Subflow Push/Pop
- [ ] `ruff check` and `ruff format` pass with zero errors
- [ ] `mypy` type-checking passes with no new errors

---

## Scope Changes

| Date | Session | Change | Reason |
|------|---------|--------|--------|
| 2026-04-22 | Session 1 | Initial product definition created | Discovery |
| 2026-04-26 | Session 2 | Refined scope from "Python project template" to "flow specification format" | Pivot based on stakeholder input |
| 2026-05-01 | Session 3 | Added session management and flow name resolution to scope; removed "Does NOT track session state"; added Agent Operators user; added Reliability, Backward Compatibility, and Usability quality attributes; updated delivery order | Domain modeling surfaced Session Tracking and CLI Flow Name Resolution as bounded contexts |