# ADR_20260426_subflow_resolution

## Status

Accepted

## Context

When a state references a subflow via its `flow` field, the CLI needs to locate the subflow YAML file and display the entry point when a transition leads to a subflow state. The lookup strategy must be simple and convention-based.

## Interview

| Question | Answer |
|---|---|
| Subflow file lookup? | The `flow` field is a relative file path (with extension) from the root flow's directory; resolve literally |
| Subflow output representation? | `<flow-name>/<first-state-id>` (e.g. `scope-cycle/idle`) — shows both which subflow and the entry state |

## Decision

Subflow lookup resolves the `flow` field as a relative path from the root flow's directory. The resolver tries the path as-is first; if the file does not exist, it appends `.yaml` and tries again. This makes the `.yaml` extension optional — flow authors can write `flow: discovery-flow` or `flow: discovery-flow.yaml`. Subflow entry is displayed as `<flow-name>/<first-state-id>`.

**Amendment (2026-05-05):** The original decision required the `.yaml` extension explicitly. This was changed because real production flows omit the extension (e.g., `flow: discovery-flow`), and requiring it added friction. The fallback-append approach keeps explicit extensions working while also supporting bare names.

## Reason

Convention-over-configuration with path flexibility; matches project layout; supports subdirectories; no extra CLI flags needed. The extension-optional fallback reduces ceremony for the common case (same directory, `.yaml` files) while preserving support for explicit paths and subdirectories.

## Alternatives Considered

- **Explicit --flows-dir flag**: over-engineered for v1; adds cognitive load
- **Walk parent directories**: fragile; could find wrong files
- **Require .yaml extension always**: original decision; rejected after production flows showed authors prefer bare names
- **Subflow output as just first state**: loses context about which subflow you're entering
- **Subflow output as just flow name**: loses context about entry point

## Consequences

- (+) Zero configuration; works with existing flow file layout
- (+) Supports subdirectories and relative paths
- (+) Clear, unambiguous output showing subflow name + entry state
- (+) `.yaml` extension is optional — bare flow names work (e.g., `flow: discovery-flow`)
- (-) Flow field has dual meaning (lookup path vs canonical flow name from loaded YAML)

## Risk Assessment

| Risk | Probability | Impact | Mitigation | Accepted? |
|------|------------|--------|------------|-----------|
| Flow field has dual meaning (lookup path vs canonical flow name) | Low | Medium | Ambiguity is mitigated by convention; loader extracts canonical name from loaded YAML | Yes |
| Bare name matches wrong file in subdirectory | Low | Low | Resolution is relative to root flow's directory; convention keeps flows flat | Yes |

## Changes

| Date | Change | Reason |
|------|--------|--------|
| 2026-04-26 | Initial decision: require `.yaml` extension | Original ADR |
| 2026-05-05 | Made `.yaml` extension optional with fallback | Production flows use bare names; requiring extension was friction (PM_20260505_subflow-mechanism-non-functional) |