# ADR-2026-04-26-condition-inlining

## Status

Accepted

## Context

Flow definitions currently require `when` guards to be declared inline on every transition. When the same set of conditions applies to multiple transitions from the same state, they must be repeated verbatim. The named-condition-groups feature adds a `conditions` field at the state level and extends `when` to accept three forms (dict, list, string), enabling reuse while remaining backwards compatible. Several design decisions were deferred to the SA: how condition groups are represented in the domain model, where resolution happens, how the three `when` forms are parsed, how resolved conditions surface to CLI and Mermaid, whether empty dict values are allowed, and whether unused groups produce warnings.

## Interview

| Question | Answer |
|---|---|
| Where does condition resolution happen? | In the loader, during `_dict_to_state`; named references are inlined into a flat dict |
| How are unknown condition references handled? | `FlowParseError` — they prevent creating a valid `GuardCondition`, consistent with the loader's structural validation role |
| How are the three `when` forms parsed? | Dict form passes through unchanged (v1); list form resolves each element (strings from conditions, dicts inline) and merges with last-entry-wins; string form is shorthand for a single-element list |
| Are empty dict values in named groups allowed? | Yes — an empty dict is a valid flat dict with zero conditions; referencing it produces an empty guard (transition always fires); YAGNI |
| Should unused condition groups produce warnings? | Yes — SHOULD-level warning, consistent with the existing unused-exit warning pattern |
| Does `GuardCondition` change? | No — after resolution, it remains a flat `dict[str, str]`; the three `when` forms are a loader concern |
| How are referenced condition groups tracked? | `Transition` gains `referenced_condition_groups: frozenset[str] \| None = None` — tracks which named groups a transition references, enabling unused-group validation |
| How are resolved conditions surfaced to Mermaid output? | Transition labels include resolved conditions as comma-separated `key: value` pairs |

## Decision

Named condition groups are resolved at load time in the loader; `GuardCondition` remains unchanged as a flat dict; `Transition` gains `referenced_condition_groups` for validation; unknown refs raise `FlowParseError`; empty dicts are allowed; unused groups produce SHOULD warnings; Mermaid shows resolved conditions on labels.

## Reason

Keeping `GuardCondition` unchanged preserves backward compatibility and simplicity; load-time resolution means downstream code (validator, CLI, Mermaid) sees only resolved flat dicts; `FlowParseError` for unknown refs is consistent with the loader's structural validation role; SHOULD warnings for unused groups mirrors the existing unused-exit pattern.

## Alternatives Considered

- **ValidationResult violations for unknown refs**: Rejected — unknown refs are structural errors that prevent creating a valid domain object, matching the loader's role; mixing them with semantic violations would conflate parse errors with spec violations
- **Separate resolution pass after loading**: Rejected — adds complexity and an extra traversal; inlining during loading is simpler and keeps the domain model clean
- **Reject empty dict values**: Rejected — YAGNI; an empty dict is a valid condition set that produces an always-true guard; no spec rule forbids it
- **No unused-group warnings**: Rejected — mirrors the existing unused-exit SHOULD pattern; helps flow authors catch typos and dead code
- **`referenced_condition_groups` on `GuardCondition`**: Rejected — condition groups are a transition-level concern (which transitions reference which groups), not a guard-level concern; placing it on `Transition` keeps validation logic simple

## Consequences

- (+) Backward compatible — v1 flows with bare-dict `when` continue to work unchanged
- (+) Simple domain model — `GuardCondition` stays a flat dict; no new entity class needed
- (+) Early error detection — unknown refs fail at load time, not at validation time
- (+) Consistent validation — unused-group warnings follow the same SHOULD pattern as unused exits
- (-) `Transition` dataclass gains a field — minimal increase in memory per transition
- (-) Loader complexity increases — three `when` forms must be parsed and resolved