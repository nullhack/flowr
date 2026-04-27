Feature: Named Condition Groups for Flow Definitions

  Flow definitions currently require `when` guards to be declared inline on
  every transition. When the same set of conditions applies to multiple
  transitions from the same state, they must be repeated verbatim. This creates
  maintenance burden and inconsistency risk. Named condition groups allow flow
  authors to define reusable condition expressions at the state level and
  reference them by name in `when` clauses, eliminating repetition while
  remaining fully backwards compatible with v1 flow definitions.

  The `conditions` field is an optional state-level dict of named condition
  groups. Each group is a flat dict of condition expressions (same syntax as
  current `when` values). The `when` field on a transition now accepts three
  forms: a bare dict (v1, unchanged), a list mixing named references (strings)
  and inline dicts (all AND-combined, later entries override earlier ones on
  key overlap), or a single string (shorthand for a list with one named
  reference). Named references must resolve to a key defined in the same
  state's `conditions` block; unknown names are a MUST-level validation error.
  No nesting (groups cannot reference other groups), no cross-state references,
  and no inheritance from parent flows or other states. The library inlines
  named references at load time, producing a flat condition dict. After
  resolution, the closed evidence schema still applies to the combined result.
  CLI `check` and Mermaid output both display resolved conditions, not named
  references. This is a minor version bump.

  Status: BASELINED (2026-04-26)

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-04-26 S4 | Q54–Q65 | Created: state-level conditions block, three when forms (dict/list/string), load-time inlining, last-entry-wins on overlap, no nesting/cross-state/inheritance, unknown refs MUST error, CLI+Mermaid show resolved conditions, minor version bump; 2 SA-deferred decisions (empty dicts, unused group warnings) |

  Rules (Business):
  - `when` accepts three forms: bare dict (v1, backwards compatible), list (strings and inline dicts, AND-combined), or single string (shorthand for list with one named reference)
  - Named references in `when` must resolve to a key in the same state's `conditions` block; unknown names are a MUST-level validation error
  - Overlapping keys in the `when` list are resolved by last-entry-wins: inline dict entries override named reference entries for the same key
  - Named condition groups are flat dicts of condition expressions only; no nesting, no referencing other groups
  - No cross-state references and no inheritance — a named group can only be referenced within the state that defines it
  - The library inlines named references at load time, producing a flat condition dict; the closed evidence schema applies to the combined result
  - CLI `check` and Mermaid output display resolved conditions, not named references
  - Flows without `conditions` continue to work unchanged; `when` as a bare dict is fully backwards compatible

  Constraints:
  - Minor version bump required
  - Two design decisions deferred to SA: empty dict values in named groups, unused condition group warnings

  Rule: Condition groups
    As a flow author
    I want to define named condition groups at the state level
    So that I can reuse condition expressions across transitions without duplication

    @id:3850fde9
    Example: State with conditions block and transitions referencing them
      Given a state defines conditions: {reviewed: {approved: "==true", score: ">=80"}}
      When a transition references reviewed via when: [reviewed]
      Then the transition's guard resolves to {approved: "==true", score: ">=80"}

    @id:70c89435
    Example: State without conditions block works unchanged
      Given a state has no conditions field
      When a transition uses when: {approved: "==true"}
      Then the flow validates and loads exactly as v1

  Rule: When forms
    As a flow author
    I want to express transition guards in three forms
    So that I can choose the most readable representation for each case

    @id:615879b8
    Example: Bare dict form is backwards compatible
      Given a transition has when: {approved: "==true"}
      When the flow is loaded
      Then the guard is {approved: "==true"} with no named references

    @id:b918281e
    Example: List form combines named references and inline dicts
      Given a state defines conditions: {reviewed: {approved: "==true"}}
      When a transition has when: [reviewed, {retry_count: "<3"}]
      Then the guard resolves to {approved: "==true", retry_count: "<3"}

    @id:4c6f2f75
    Example: Single string form is shorthand for list with one named reference
      Given a state defines conditions: {reviewed: {approved: "==true"}}
      When a transition has when: reviewed
      Then the guard resolves to {approved: "==true"}

  Rule: Overlapping keys
    As a flow author
    I want inline conditions to override named group conditions
    So that I can specialise a generic condition group for a specific transition

    @id:959366c4
    Example: Inline dict key overrides named group key
      Given a state defines conditions: {reviewed: {approved: "==true", score: ">=80"}}
      When a transition has when: [reviewed, {approved: "==false"}]
      Then the guard resolves to {approved: "==false", score: ">=80"}

  Rule: Reference validation
    As a flow author
    I want invalid condition references to be caught at load time
    So that I get a clear error instead of silent misconfiguration

    @id:400fa5ad
    Example: Unknown named reference is a validation error
      Given a state defines conditions: {reviewed: {approved: "==true"}}
      When a transition references when: [missing_ref]
      Then the flow fails validation with an error naming the unknown reference

  Rule: Scope and isolation
    As a flow author
    I want condition groups to be scoped to their defining state
    So that I can reason locally about each state's guards

    @id:49a58755
    Example: Condition groups cannot reference groups from other states
      Given state A defines conditions: {reviewed: {approved: "==true"}}
      And state B has no conditions block
      When state B has a transition with when: [reviewed]
      Then the flow fails validation because reviewed is not defined in state B

  Rule: Resolved output
    As a flow author
    I want check and mermaid to display resolved conditions
    So that I can see the actual guard expressions without manual resolution

    @id:a159b526
    Example: Check command shows resolved flat conditions
      Given a state defines conditions: {reviewed: {approved: "==true", score: ">=80"}}
      And a transition has when: [reviewed]
      When the user runs flowr check on the flow
      Then the output shows the transition guard as {approved: "==true", score: ">=80"}

    @id:6d5dddcc
    Example: Mermaid output shows resolved conditions
      Given a state defines conditions: {reviewed: {approved: "==true"}}
      And a transition has when: [reviewed]
      When the user runs flowr mermaid on the flow
      Then the transition label shows approved: ==true