# ADR-2026-04-26-validation-result

## Status

Accepted

## Context

The feature defines conformance levels (MUST/SHOULD) and Examples show the validator classifying violations by severity (e.g., "the validator reports a MUST-level error" vs "the validator reports a SHOULD-level warning"). The validator must collect all violations rather than failing on the first one, so users get a complete picture of issues in their flow definitions.

## Interview

| Question | Answer |
|---|---|
| Should the validator return a result type, raise exceptions, or return a list? | Return a ValidationResult type containing a list of Violation objects |
| How should violations be structured? | Each Violation has severity (MUST/SHOULD), message, and location |
| Should validation be a single function or composable rules? | Single `validate()` function that composes individual rule checks internally |

## Decision

The validator returns a `ValidationResult` containing a list of `Violation` objects, each with `severity` (ConformanceLevel enum: MUST or SHOULD), `message` (human-readable), and `location` (where in the flow definition). `ValidationResult` provides convenience methods: `errors` (MUST violations), `warnings` (SHOULD violations), and `is_valid` (True if no MUST violations).

## Reason

Collecting all violations gives users a complete picture; a result type with convenience methods is more ergonomic and self-documenting than a bare list or exceptions.

## Alternatives Considered

- **Raise ValidationException**: rejected — only captures the first violation; users need all violations
- **Bare list of tuples**: rejected — tuples aren't self-documenting; callers must remember positions
- **Result type (success/errors)**: rejected — doesn't distinguish MUST from SHOULD severity levels

## Consequences

- (+) Users see all violations at once, not just the first
- (+) Clear, self-documenting types with named fields
- (+) Easy to filter by severity (errors vs warnings)
- (-) Slightly more types to define (ValidationResult, Violation, ConformanceLevel)
- (-) Callers must check `is_valid` rather than catching an exception