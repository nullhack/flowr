Feature: Export Viz Pipeline

  Enrich JSON export with viz-required metadata (version, exits, subflow fields)
  and restructure directory export as a named collection so that downstream tools
  (like the D3 visualizer) can render complete flow information without additional
  lookups or duplicated parsing.

  Status: ELICITING

  Rules (Business):
  - JSON single-flow export must include `version` and `exits` from the Flow domain object, and subflow-state nodes must include `subflow` and `subflowVersion` fields
  - JSON directory export must change from `[{...}]` array to `{"defaultFlow": "...", "flows": [...]}` object so downstream tools can identify the entry-point flow

  Constraints:
  - This feature MODIFIES existing export-json behavior — existing tests (99a274dd, unit/export_test.py directory tests) must be updated to match the new output shape
  - Zero new runtime dependencies introduced
  - No changes to existing domain types (Flow, State, Transition, GuardCondition)

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-07 planning | — | Created: feature breakdown from stakeholder specification |

  Rule: JSON single-flow enrichment
    As a tool author
    I want the JSON single-flow export to include version, exits, and subflow metadata
    So that downstream tools (like the D3 visualizer) can render complete flow information without additional lookups or duplicated parsing

    @id:a1c3e5f7
    Example: Single-flow export includes version and exits fields
      Given a flow definition with version "1.0.20260507" and exits ["done", "failed"]
      When the user runs `flowr export --format json examples/simple.yaml`
      Then the JSON output contains a `version` field matching "1.0.20260507" and an `exits` field matching ["done", "failed"]

    @id:b2d4f6a8
    Example: Subflow-state nodes include subflow and subflowVersion
      Given a flow where state "drill-down" has `flow: child-flow` and `flow_version: 2.0.0`
      When the user runs `flowr export --format json main.yaml`
      Then the node for "drill-down" includes `"subflow": "child-flow"` and `"subflowVersion": "2.0.0"`

    @id:c3e5f7a9
    Example: Non-subflow state nodes omit subflow fields
      Given a flow with states that have no `flow` field
      When the user runs `flowr export --format json examples/simple.yaml`
      Then no node in the output contains a `subflow` or `subflowVersion` field

  Rule: JSON directory export restructured as named collection
    As a tool author
    I want the JSON directory export to produce a structured object with a `defaultFlow` key and a `flows` array
    So that downstream tools can identify the entry-point flow without hardcoding assumptions

    @id:d4f6a8b0
    Example: Directory export produces object with defaultFlow and flows array
      Given a directory `flows/` contains `alpha.yaml` and `beta.yaml`
      When the user runs `flowr export --format json flows/`
      Then the output is a JSON object (not array) with a `defaultFlow` key and a `flows` key containing an array of flow entries sorted alphabetically by filename

    @id:e5f7a9b1
    Example: defaultFlow selects main-flow when present
      Given a directory contains `main-flow.yaml` and `other.yaml`
      When the user runs `flowr export --format json flows/`
      Then the `defaultFlow` value is `"main-flow"`

    @id:f6a8b0c2
    Example: defaultFlow falls back to alphabetically first flow name
      Given a directory contains `beta.yaml` and `gamma.yaml` but no `main-flow.yaml`
      When the user runs `flowr export --format json flows/`
      Then the `defaultFlow` value is `"beta"`
