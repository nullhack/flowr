Feature: Export Mermaid

  Mermaid export adapter producing valid stateDiagram-v2 output, with condition-label control
  and per-adapter CLI flags. Extends the export-core foundation.

  Status: BASELINED (2026-05-06)

  Constraints:
  - Output must be valid Mermaid stateDiagram-v2
  - `to_mermaid()` may be extended with an options parameter but its existing signature must remain backward-compatible
  - Zero new runtime dependencies

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q1 | How to handle `--no-conditions` given `to_mermaid()` has no options parameter? | Resolved | Extend `to_mermaid()` with an optional options dict parameter |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-06 planning | — | Created: split from export.feature for INVEST compliance |

  Rule: Mermaid single-flow export
    As a developer
    I want to export a single flow as a Mermaid stateDiagram-v2
    So that I can render flow definitions as state diagrams

    @id:a2045d96
    Example: Single flow produces valid stateDiagram-v2
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format mermaid examples/simple.yaml`
      Then the output is a valid Mermaid stateDiagram-v2 string identical to the previous `flowr mermaid` output

    @id:67b1b50c
    Example: No-conditions mode strips condition labels
      Given a flow definition with guarded transitions
      When the user runs `flowr export --format mermaid --no-conditions examples/simple.yaml`
      Then the output is a valid stateDiagram-v2 without condition labels on transition edges

  Rule: Mermaid directory export
    As a developer
    I want to export all flows from a directory as separated Mermaid diagrams
    So that I can visualize an entire workflow suite

    @id:2e068a23
    Example: Directory export separates each flow with a separator
      Given a directory `flows/` contains `alpha.yaml` and `beta.yaml`
      When the user runs `flowr export --format mermaid flows/`
      Then the output contains a stateDiagram-v2 for each flow separated by `---`

  Rule: Per-adapter CLI flags
    As a CLI user
    I want each adapter to define its own command-line flags
    So that I can control format-specific options without cluttering the shared interface

    @id:1d5ba172
    Example: JSON adapter flags appear in help
      When the user runs `flowr export --format json --help`
      Then the help text includes `--flat` and `--no-attrs` options

    @id:0ce7099f
    Example: Mermaid adapter flags appear in help
      When the user runs `flowr export --format mermaid --help`
      Then the help text includes `--no-conditions` option
