# ADR_20260426_evidence_type_system

## Status

Accepted

## Context

YAML parses `true` as Python `True` (boolean), `false` as `False`, and numeric strings like `80` as integers. Condition expressions in `when` clauses are always strings (e.g., `==true`, `>=80%`). The spec and feature file explicitly deferred the evidence type system to the architect (Constraint: "Evidence type system is deferred to the architect at Step 2"). The question is how YAML-typed evidence values compare with string condition expressions.

## Interview

| Question | Answer |
|---|---|
| When a condition says `==true`, should it match the YAML boolean `True` or the string `"true"`? | Coerce evidence values to strings; YAML `True` becomes `"true"` (lowercase) |
| When a condition says `>=80`, should it compare against the YAML integer `80` or the string `"80"`? | Coerce to string `"80"`, then numeric extraction strips and compares |
| How should the validator handle YAML's automatic type coercion (`yes`, `no`, `on`, `off` → booleans)? | All YAML-typed values are coerced to their string representation before comparison |

## Decision

All evidence values are coerced to strings before comparison: YAML booleans become lowercase (`True` → `"true"`, `False` → `"false"`), YAML numbers become numeric strings (`80` → `"80"`).

## Reason

Eliminates type confusion from YAML's automatic coercion; conditions are pattern strings and evidence is always string-matched, giving a simple and predictable type model.

## Alternatives Considered

- **Preserve YAML types with smart comparison**: adds complexity and ambiguity (e.g., does `==true` match both `True` and `"true"`?)
- **Require string quoting in YAML for all condition-relevant values**: violates YAML ergonomics and common practice
- **Type-agnostic comparison with per-operator coercion rules**: too complex for v1

## Consequences

- (+) Simple, predictable type model
- (+) Users reason about conditions as string patterns
- (+) No YAML type coercion surprises
- (-) Users must remember YAML `true`/`false`/`yes`/`no` become strings
- (-) Numeric extraction still applies for `>=`, `<=`, `>`, `<` operators (on string representations)

## Risk Assessment

| Risk | Probability | Impact | Mitigation | Accepted? |
|------|------------|--------|------------|-----------|
| Users may forget YAML type coercion rules (true/false/yes/no) | Medium | Low | Document in glossary and CLI help; numeric extraction applies to string representations | Yes |