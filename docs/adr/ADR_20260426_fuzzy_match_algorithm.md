# ADR_20260426_fuzzy_match_algorithm

## Status

Accepted

## Context

The spec and glossary define `~=` as "case-insensitive substring match with small typo tolerance" for strings and "5% tolerance" for numbers. The feature file deferred the exact algorithm to the architect (Constraint: "Fuzzy match algorithm for ~= operator is deferred to the architect at Step 2"). The stakeholder decided that string fuzzy matching is too complicated and prone to interpretation, and chose to make `~=` numbers-only.

## Interview

| Question | Answer |
|---|---|
| What algorithm implements "small typo tolerance" for string matching? | Not applicable — `~=` is numbers-only |
| Should we use an external library for fuzzy matching? | No — `~=` is numbers-only with simple percentage tolerance |
| What is the numeric tolerance threshold? | 5% — the condition passes if `\|evidence - condition\| / condition ≤ 0.05` |

## Decision

The `~=` operator applies ONLY to numeric values. A `~=` condition passes if the absolute difference between the evidence and condition values, divided by the condition value, is at most 0.05 (5% tolerance). Numeric extraction still strips non-numeric suffixes from both sides before comparison. For strings, `~=` is not a valid operator — use `==` for exact match or `!=` for inequality.

## Reason

Eliminates the complexity and ambiguity of string fuzzy matching; numeric 5% tolerance is simple, deterministic, and well-defined.

## Alternatives Considered

- **Levenshtein ≤ 1 for string typo tolerance**: rejected by stakeholder as too complicated and prone to interpretation
- **Pure substring containment (no typo tolerance) for strings**: rejected — stakeholder chose to remove string matching entirely
- **External library (python-Levenshtein, fuzzywuzzy)**: rejected — adds runtime dependency for an algorithm that is no longer needed for strings

## Consequences

- (+) Simple, deterministic, no Levenshtein implementation needed
- (+) No external dependencies needed
- (+) No ambiguity about what "small typo tolerance" means
- (-) No string fuzzy matching capability (strings must use `==` or `!=`)
- (-) Two existing Examples (`@id:bdd51f94`, `@id:7711a3c7`) need deprecation and replacement with numeric Examples

## Risk Assessment

| Risk | Probability | Impact | Mitigation | Accepted? |
|------|------------|--------|------------|-----------|
| No string fuzzy matching capability; users must use == or != | Low | Low | ~= for strings was never implemented; explicit == and != are clearer | Yes |