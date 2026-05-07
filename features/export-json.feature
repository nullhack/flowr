Feature: Export JSON

  JSON export adapter producing structured nodes-and-edges output with nested subflow entries,
  flat-mode inlining, and attrs control. Extends the export-core foundation.

  Status: BASELINED (2026-05-06)

  Constraints:
  - JSON output must be valid and parseable
  - Zero new runtime dependencies (uses stdlib json module)
  - No modifications to existing domain types

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q1 | Should JSON output be formally validated against a schema? | Resolved | Tests only — schema validation deferred |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-06 planning | — | Created: split from export.feature for INVEST compliance |

  Rule: JSON single-flow export
    As a tool author
    I want to export a single flow as structured JSON with nodes and edges
    So that I can programmatically consume flow definitions in downstream tooling

    @id:f8eb4019
    Example: Default nested mode produces separate subflow entries
      Given a flow `main.yaml` references a subflow via `flow: child`
      When the user runs `flowr export --format json main.yaml`
      Then the output contains separate flow entries for `main` and `child`, and a `defaultFlow` key indicating the root

    @id:7187f2ad
    Example: Flat mode inlines subflow states with prefixed IDs
      Given a flow `main.yaml` references a subflow via `flow: child`
      When the user runs `flowr export --format json --flat main.yaml`
      Then all subflow states are merged into the root flow's nodes list with prefixed IDs

    @id:f79514e5
    Example: No-attrs mode omits state attributes
      Given a flow definition with states containing `attrs`
      When the user runs `flowr export --format json --no-attrs examples/simple.yaml`
      Then the output JSON omits the `attrs` field from all nodes

  Rule: JSON directory export
    As a tool author
    I want to export all flows from a directory as a JSON collection
    So that I can process multiple flow definitions in a single structured output

    @id:99a274dd
    Example: Directory export produces a collection with defaultFlow
      Given a directory `flows/` contains `alpha.yaml` and `beta.yaml`
      When the user runs `flowr export --format json flows/`
      Then the output is a JSON array of flow entries sorted alphabetically, with a top-level `defaultFlow` key
