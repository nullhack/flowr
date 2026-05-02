# Flow Definition Specification v1

This document is the authoritative specification for the flow definition YAML format. It consolidates the v1 design based on analysis of 10 industry standards (XState, SCXML, Serverless Workflow, BPMN 2.0, `transitions` Python, SMC, Harel Statecharts, ASL, Temporal, GitHub Actions).

**Key decision:** Keep the YAML format. No FOSS standard covers the format's core features (per-state agent assignment, AI-agent-as-runtime, filesystem-as-source-of-truth). Instead, formalize the existing format with clarifications and add tooling (validation, Mermaid converter).

---

## Top-Level Fields

| Field | Required | Description |
|-------|----------|-------------|
| `flow` | yes | Unique name string, used for subflow references |
| `version` | yes | Semver (e.g., `1.2.0`) |
| `params` | no | List of parameter declarations. Plain strings are required params (e.g., `params: [feature_slug]`). Object mappings provide defaults (e.g., `params: [{name: verbose, default: false}]`). Missing required params are validation errors. |
| `exits` | yes | List of exit names — the contract this flow offers to parent flows |
| `attrs` | no | Opaque dict for project-specific data; the library ignores this entirely |
| `states` | yes | Ordered list of state objects; first state is the initial state |

---

## Examples

### Minimal Flow

The smallest valid flow: one state, one exit, no conditions.

```yaml
flow: ping
version: 1.0.0
exits: [done]

states:
  - id: start
    next:
      go: done
```

### Flow with Params and Attrs

A flow that declares parameters (required and optional with defaults) and attaches opaque project-specific data.

```yaml
flow: deploy
version: 1.2.0
params:
  - environment
  - region
  - name: verbose
    default: false
exits: [deployed, failed]
attrs:
  owner: platform-team
  slack_channel: "#deploys"

states:
  - id: prepare
    next:
      ready: execute

  - id: execute
    next:
      success: deployed
      error: failed
```

### Guarded Transitions

Transitions with `when` conditions. Evidence must match the condition keys.

```yaml
flow: review
version: 1.0.0
exits: [approved, rejected]

states:
  - id: pending
    next:
      submit: under-review

  - id: under-review
    next:
      approve:
        to: approved
        when: { score: ">=80%", verdict: "~=pass" }
      reject:
        to: rejected
        when: { verdict: "!=pass" }
```

Actor sends trigger `approve` with evidence `{ score: "92%", verdict: "passing" }` → condition `>=80%` extracts 92 vs 80 (pass), `~=pass` fuzzy-matches "passing" (pass) → transition fires.

### Within-Flow Cycle

A state that loops back to itself or an earlier state.

```yaml
flow: scope-cycle
version: 1.0.0
params: [feature_slug]
exits: [complete, blocked]

states:
  - id: discovery
    next:
      baselined: stories
      more-discovery: discovery

  - id: stories
    next:
      stories-committed: complete
```

`discovery → discovery` is a within-flow cycle — allowed.

### Subflow Invocation

A parent flow that invokes a child flow via `flow:` on a state. Parent `next` keys must match the child's `exits`.

Parent:

```yaml
flow: feature-flow
version: 1.0.0
params: [feature_slug, branch_name]
exits: [complete, blocked]
attrs:
  agents:
    idle: product-owner
    step-1-scope: product-owner
    step-2-arch: system-architect

states:
  - id: idle
    next:
      select-feature: step-1-scope

  - id: step-1-scope
    flow: scope-cycle
    flow-version: "^1"
    next:
      complete: step-2-arch
      blocked: idle

  - id: step-2-arch
    next:
      complete: complete
      blocked: step-1-scope
```

Child (`scope-cycle` exits are `[complete, blocked]` — matching parent's `next` keys):

```yaml
flow: scope-cycle
version: 1.0.0
params: [feature_slug]
exits: [complete, blocked]

states:
  - id: discovery
    next:
      baselined: stories
      more-discovery: discovery

  - id: stories
    next:
      stories-committed: complete
```

### State-Level Attrs Replace Flow-Level

```yaml
flow: ci-pipeline
version: 1.0.0
exits: [passed, failed]
attrs:
  timeout: 300
  retry: 2

states:
  - id: build
    attrs:
      timeout: 600
      docker: true
    next:
      ok: test

  - id: test
    next:
      ok: passed
      fail: failed
```

In state `build`, `attrs` is `{ timeout: 600, docker: true }` — the flow-level `{ timeout: 300, retry: 2 }` is entirely replaced, not merged. `retry` is absent and `timeout` is overridden.

---

## State Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Unique identifier within this flow |
| `next` | yes* | Trigger → target mapping; required unless the state only references exits |
| `flow` | no | If present, makes this state a subflow invocation |
| `flow-version` | no | Semver constraint for the referenced flow (e.g., `"^1"`) |
| `attrs` | no | Opaque dict for state-specific data; **replaces flow-level attrs entirely** (no merge, no deep merge) |
| `when` | no | Guard conditions on a transition (see Condition Syntax) |

\*States must have `next` or be referenced only by exit targets.

---

## Transition Format (`next` values)

Three forms:

| Form | Syntax | Description |
|------|--------|-------------|
| Simple | `approved: step-5` | String target, no conditions |
| Guarded | `approved: { to: step-5, when: {...} }` | Mapping with conditions |
| Mixed | Both in same `next` | Simple and guarded targets coexist |

Guarded transitions use `when` — a dict of condition expressions, AND-combined. **No inheritance:** every condition must be explicitly declared.

---

## Exit System

- `exits` is a flat list at flow level, **always required**
- Any state can reference an exit name in its `next` map: `cancel: cancelled`
- The library resolves `next` targets at load time: found in states → internal transition; found in exits → subflow exit
- A `next` target that matches **both** a state id and an exit name is a **validation error** (ambiguous reference)
- Every `next` target must resolve to either a state id or an exit name (never neither)
- Multiple exits can map to the same parent state: `rejected: step-3` / `cancelled: step-3`

---

## Condition Syntax

The `when` dict uses expression strings as values:

| Operator | Meaning | Example |
|----------|---------|---------|
| `==value` | Equality match | `==true`, `==pass` |
| `!=value` | Inequality match | `!=false` |
| `>=N` | Greater than or equal | `>=80%` (compares 80) |
| `<=N` | Less than or equal | `<=5` |
| `>N` | Greater than | `>0` |
| `<N` | Less than | `<3` |
| `~=value` | Approximate numeric match | `~=100` — passes if evidence value is within 5% of condition value (numeric extraction applies) |

Numeric portion is extracted from **both** condition and evidence values before comparison (e.g., `>=80%` vs evidence `75%` → compares 80 vs 75).

Plain strings without operators are treated as `==value`. Evidence keys must exactly match `when` keys — closed schema, no extra or missing keys.

**Note:** All evidence values are coerced to strings before comparison. YAML booleans become lowercase (`True` → `"true"`, `False` → `"false"`), YAML numbers become numeric strings (`80` → `"80"`). The `~=` operator applies ONLY to numeric values (5% tolerance); it is not valid for string matching. See ADR_20260426_evidence_type_system and ADR_20260426_fuzzy_match_algorithm.

---

## Subflow Model

- `flow: <name>` on a state makes it a subflow (no `type` field needed)
- `flow-version: "^1"` constrains which versions are compatible
- Parent `next` keys must match child's `exits` list exactly
- Subflows use a call-stack mechanism: push on entry, pop on exit
- Context is isolated: only current flow visible in responses

---

## Semver for Flows

| Change | Version impact |
|--------|----------------|
| Adding a new exit | Minor bump |
| Adding states or requirements | Patch (non-breaking) |
| Removing or renaming exits | Major (breaking) |

Parent flows constrain compatibility: `flow-version: "^1"`

---

## Cycle Rules

- **Within-flow cycles are allowed** (e.g., `idle → working → idle`)
- **Cross-flow cycles are forbidden** (detected via DFS at load time)

---

## Validation Rules (Load-Time)

1. Every `next` target resolves to a state id or an exit name
2. No `next` target is ambiguous (matches both a state id and an exit name)
3. Parent `next` keys match child's `exits` list exactly
4. No cross-flow cycles (DFS detection)
5. Exit names in `exits` must have at least one state referencing them
6. Params without defaults must be provided at flow invocation time

---

## Conformance Levels

- **MUST** — required for all conforming implementations (e.g., immutable loaded flows, validation rules above)
- **SHOULD** — recommended but optional (e.g., filesystem wins over session cache on conflict)

---

## Session Format (Minimal — v1)

```yaml
session: a1b2c3d4-...
started: "2026-04-25T10:00:00Z"
current:
  flow: arch-cycle
  state: interview
  stack:
    - flow: feature-flow
      state: step-2-arch
params:
  feature-flow:
    feature_slug: user-auth
    branch_name: feat/user-auth
  arch-cycle:
    feature_slug: user-auth
    branch_name: feat/user-auth
```

Fields: `session` (UUID), `started` (ISO 8601), `current` (flow + state), `stack` (for subflows; push on entry, pop on exit), `params` (per-flow variable namespace).

**Note:** Transition counts and history tracking are **not included** in v1.

---

## Transition Protocol

1. Actor sends a **trigger** (transition name) plus **evidence** (key-value dict matching `when` keys).
2. Library validates: transition exists from current state, evidence keys match, each condition expression is satisfied.
3. **Valid**: session `current` updates, session file persisted.
4. **Invalid**: warning returned, no state change.

---

## Design Principles

1. **Immutable loaded flows** — edits produce copies (MUST)
2. **Closed evidence schema** — keys must exactly match
3. **Isolated subflow context** — only current flow visible
4. **Session truth assumption** — filesystem wins over session (SHOULD)
5. **Thin enforcement** — validate only, no execution
6. **No auto-rollback** — no transition limits

---

## v1 Out of Scope

- Jinja/string templating or `${param}` interpolation
- `type` field on states (removed; `flow` presence implies subflow)
- Named requirement groups (removed; `when` is always inline)
- Condition inheritance (removed; all conditions explicit)
- Auto-rollback, transition attempt limits, session history
- Parallel/fork-join states
- Action execution
- Runtime engine
- Transition count tracking
- JSON Schema deliverable (internal representation uses Python dataclasses; JSON is for CLI communication only)

---

## Changes from Original Spec

| Original | v1 | Rationale |
|----------|-----|-----------|
| `type: normal/subflow` | Removed; `flow` presence implies subflow | Redundant field |
| `requires` (state-level) | `when` (transition-level) | Guards belong on transitions, not states |
| Named requirement groups | Inline `when` dicts | Simplification; no inheritance confusion |
| `else` keyword | Removed; exits are just targets | No special treatment for fallbacks |
| `params` (state-level) | `attrs` (opaque) | Library doesn't inspect params; make them opaque |
| `agent` (state-level) | `attrs` (opaque) | Project-specific, not a library concern |
| `exits` conditional | `exits` always required | Exits are a contract; must be declared |
| No `version` | `version` required | Enables semver compatibility checks |
| No `~=` operator | `~=` added | Fuzzy match for approximate comparisons |