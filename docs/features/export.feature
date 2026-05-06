Feature: Export

  Replaces `flowr mermaid` with a unified `flowr export --format <format>` command backed by a
  pluggable adapter architecture. Ships two built-in adapters: JsonExporter (structured nodes and
  edges) and MermaidExporter (stateDiagram-v2). Each adapter defines its own CLI flags, and the
  system auto-detects file vs directory input for single-flow or multi-flow collection export.

  Status: ELICITING

  Rules (Business):
  - The `export` subcommand requires a `--format` argument; the format name is resolved to an adapter via the hardcoded EXPORTERS registry before any file I/O occurs (fail-fast on unknown formats)
  - The CLI auto-detects whether the input path is a file or directory; directories trigger directory-mode export, files trigger single-flow export
  - The input path must exist on disk; a non-existent path produces a clear error before loading begins
  - Each adapter defines its own CLI flags through `add_arguments()`; flags are adapter-specific and parsed into an adapter options dict
  - In file mode, the resolved adapter's `export()` method produces output for a single loaded flow
  - In directory mode, the resolved adapter's `export_directory()` method produces output for all flows in the directory as a collection; flows are sorted alphabetically by filename for deterministic output
  - The `mermaid` standalone subcommand is removed entirely; `flowr export --format mermaid` is the replacement path
  - JsonExporter produces structured JSON with nodes (type: state/subflow/exit) and edges (kind: transition/exit); named condition groups are resolved into flat condition dicts; subflows appear as separate flow entries by default; `--flat` inlines subflow states with prefixed IDs; `--no-attrs` omits state attrs; directory mode includes a `defaultFlow` key
  - MermaidExporter produces a valid stateDiagram-v2 string per flow, delegating to the existing `to_mermaid()` function; directory mode separates each flow's diagram with `---`; `--no-conditions` strips condition labels from transition edges
  - The ExportRegistry is hardcoded at module load time (dict of format name → adapter instance); no runtime registration, no entry points; third-party extensibility is a future concern
  - No modifications to existing domain types (Flow, State, Transition, GuardCondition) or loader functions; the export feature only consumes them

  Constraints:
  - Zero new runtime dependencies introduced (QA6 from interview)
  - CLI exit codes follow existing convention: 0 = success, 1 = command failed, 2 = usage error (ADR_20260426_cli_io_convention)
  - CLI output: stdout for results, stderr for errors/warnings (ADR_20260426_cli_io_convention)
  - Test coverage ≥ 80% per project DoD; all new adapter code and mermaid subcommand removal must be covered
  - Backward compatibility: existing `flowr mermaid` users must migrate to `flowr export --format mermaid` (QA4 — breaking change accepted by stakeholder)
  - Extensibility: adding a new export format requires implementing the FlowExporter Protocol and registering in the EXPORTERS dict (QA1)

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q1 | How should MermaidExporter handle `--no-conditions` given that `to_mermaid()` does not currently accept options? Post-process the output string, or add an options parameter to `to_mermaid()`? | Open | Assumed: post-process output or extend to_mermaid — resolved during architecture |
  | Q2 | Should the JSON output schema be formally validated (e.g., against a JSON Schema), or is structural correctness enforced through tests alone? | Open | Assumed: tests only — schema validation deferred per event storming G2 |
  | Q3 | Should `flowr export` with no `--format` flag default to a format, or require it explicitly? | Open | Assumed: `--format` is required — no default |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-06 IN_20260506 | — | Created: initial feature discovery from interview, event storming, and domain model |
