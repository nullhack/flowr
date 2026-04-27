# ADR-2026-04-26-subflow-resolution

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

Subflow lookup resolves the `flow` field as a relative path from the root flow's directory, including file extension. Subflow entry is displayed as `<flow-name>/<first-state-id>`.

## Reason

Convention-over-configuration with path flexibility; matches project layout; supports subdirectories; no extra CLI flags needed.

## Alternatives Considered

- **Explicit --flows-dir flag**: over-engineered for v1; adds cognitive load
- **Walk parent directories**: fragile; could find wrong files
- **Auto-append .yaml extension**: adds magic; explicit extension is simpler
- **Subflow output as just first state**: loses context about which subflow you're entering
- **Subflow output as just flow name**: loses context about entry point

## Consequences

- (+) Zero configuration; works with existing flow file layout
- (+) Supports subdirectories and relative paths
- (+) Clear, unambiguous output showing subflow name + entry state
- (-) Flow field must include `.yaml` extension — existing reference YAML files need updating
- (-) Flow field has dual meaning (lookup path vs canonical flow name from loaded YAML)
