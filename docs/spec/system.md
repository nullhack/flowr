# System Overview: flowr

> Current-state description of the production system.
> Updated by the Software Architect when domain understanding changes (rare).
> Contains only completed features — nothing from backlog or in-progress.
> This document captures what code cannot express: WHY contexts exist, HOW they relate, WHAT the aggregate boundaries are and why.

---

## Summary

flowr is a Python library and CLI for defining, validating, and visualizing non-deterministic state machine workflows in YAML. It provides a reference validator that checks flow definitions against the specification, a Mermaid converter that generates stateDiagram-v2 diagrams, and a CLI with six subcommands (validate, states, check, next, transition, mermaid) for one-shot flow definition interaction. Named condition groups allow flow authors to define reusable condition expressions at the state level and reference them by name in `when` clauses, eliminating repetition while remaining fully backwards compatible. The system uses Python dataclasses for its internal representation and PyYAML for parsing flow definition files.

---

## Delivery

**Mechanism:** CLI / Library

Developers interact via the CLI (`python -m flowr <subcommand>`) or the Python API. Both humans and machines write and validate flows; the CLI is human-facing, the library is machine-facing.

---

## Context (C4 Level 1)

### Actors

| Actor | Description |
|-------|-------------|
| `Developer` | Python engineer using flowr to define and validate workflows |
| `Tool Author` | Engineer building tools that validate or convert flow definitions |
| `CLI User` | Developer or operator running flowr subcommands from the terminal |

### Systems

| System | Kind | Description |
|--------|------|-------------|
| `flowr` | Internal | Python library for flow definition validation, conversion, and CLI access |
| `YAML Source` | External | Flow definition files on disk that flowr loads and validates |

### Interactions

| Interaction | Behaviour | Technology |
|-------------|-----------|------------|
| Developer → flowr | Loads, validates, and converts flow definitions | Python API |
| Developer → flowr CLI | Runs `python -m flowr --help` / `--version` | CLI / subprocess |
| CLI User → flowr CLI | Runs subcommands on flow definition files | CLI / subprocess |
| Tool Author → flowr | Builds validation and conversion tools on top of flowr | Python API |
| flowr → YAML Source | Reads flow definition files from disk | PyYAML |

---

## Container (C4 Level 2)

### Boundary: flowr

| Container | Technology | Responsibility |
|-----------|------------|----------------|
| CLI Entrypoint | Python / argparse | Parses subcommands and flags; dispatches to domain operations; formats output |
| Flow Definition Domain | Python / dataclasses | Core domain types for flow definitions, states, transitions, conditions, params, and attrs |
| Validator | Python / dataclasses | Validates flow definitions against the specification; returns ValidationResult with Violations |
| Mermaid Converter | Python | Converts flow definitions to Mermaid stateDiagram-v2 format |
| Flow Loader | Python / PyYAML | Parses YAML files into Flow domain objects; resolves subflow references by relative path; inlines named condition groups at load time |

### Interactions

| Interaction | Behaviour |
|-------------|-----------|
| CLI User → CLI Entrypoint | Invokes via `flowr <subcommand>` or `python -m flowr <subcommand>` |
| Developer → CLI Entrypoint | Invokes via `python -m flowr` |
| CLI Entrypoint → Flow Loader | Loads root flow, resolves subflow references, and inlines named condition groups |
| CLI Entrypoint → Validator | Runs validate subcommand |
| CLI Entrypoint → Mermaid Converter | Runs mermaid subcommand |
| Validator → Flow Definition Domain | Reads domain types to validate structure and semantics |
| Mermaid Converter → Flow Definition Domain | Reads domain types to generate diagram output |
| Flow Loader → YAML Source | Reads YAML files from disk |

---

## Module Structure

| Module | Responsibility | Bounded Context |
|--------|----------------|-----------------|
| `flowr/__main__.py` | CLI entrypoint: builds argparse parser with subcommands; dispatches; formats output; exit codes | CLI |
| `flowr/__init__.py` | Package marker; no public API | CLI |
| `flowr/cli/__init__.py` | CLI subpackage marker | CLI |
| `flowr/cli/output.py` | Output formatting: text and JSON formatters for CLI results | CLI |
| `flowr/domain/__init__.py` | Domain subpackage marker | Flow Definition |
| `flowr/domain/flow_definition.py` | Core domain types: Flow, State, Transition, GuardCondition, ConditionExpression, Param; State carries optional named condition groups; Transition tracks referenced condition groups | Flow Definition |
| `flowr/domain/validation.py` | Validation types: ConformanceLevel, Violation, ValidationResult; validate function; condition reference and unused group checks | Flow Definition |
| `flowr/domain/condition.py` | Condition evaluation: ConditionOperator enum, evaluate_condition function | Flow Definition |
| `flowr/domain/mermaid.py` | Mermaid stateDiagram-v2 conversion: to_mermaid function; shows resolved conditions on transition labels | Flow Definition |
| `flowr/domain/session.py` | Session format: Session, SessionStack types | Flow Definition |
| `flowr/domain/loader.py` | YAML parsing Protocol and load_flow function; subflow resolution; condition inlining via resolve_when_clause | Flow Definition |

---

## Domain Model Documentation

### Why Each Context Exists

| Bounded Context | Business Capability | Why It's Separate |
|-----------------|---------------------|-------------------|
| `CLI` | Expose the application as a command-line tool with 6 subcommands; parse args; format and display results | The CLI is a delivery mechanism — a driving adapter — that depends on the domain. It has no business logic of its own and can be replaced without touching the domain. |
| `Flow Definition` | Define, validate, and convert non-deterministic state machine workflows in YAML | This is the core domain — the reason the product exists. It owns all domain types and invariants. Separating it from CLI ensures the domain is testable and reusable without the CLI layer. |

### Aggregate Boundary Rationale

| Aggregate | Why These Entities Are Grouped | Transactional Invariant |
|-----------|-------------------------------|------------------------|
| Flow | A Flow is the root entity of a flow definition; all States, Transitions, and Conditions belong to a single Flow and are loaded and validated together | A Flow must be self-consistent: all next targets resolve to valid states or exits, no cross-flow cycles exist, and all condition references resolve |
| Session | A Session tracks the current flow and state for a one-shot CLI invocation; it has no persistence requirement | A Session's (flow, state) pair must reference a valid state within a loaded flow |

---

## Active Constraints

- PyYAML is the only runtime dependency — all flow definition parsing uses `yaml.safe_load`
- All evidence values are coerced to strings before condition evaluation (ADR_20260422_cli_parser_library)
- The ~= operator applies ONLY to numeric values (5% tolerance); no string fuzzy matching (ADR_20260426_fuzzy_match_algorithm)
- Validator returns ValidationResult with Violation list — no exceptions for validation failures (ADR_20260426_validation_result)
- Version format is calver (`major.minor.YYYYMMDD`); tests must not assume semver
- CLI exit codes: 0 = success, 1 = command failed, 2 = usage error (ADR_20260426_cli_io_convention)
- CLI output: stdout for results, stderr for errors/warnings (ADR_20260426_cli_io_convention)
- Evidence input: `--evidence key=value` for simple, `--evidence-json` for complex (ADR_20260426_cli_io_convention)
- Subflow lookup: `flow` field is relative file path from root flow directory, including extension (ADR_20260426_subflow_resolution)
- Named condition groups are inlined at load time; after resolution, GuardCondition remains a flat dict; unknown refs raise FlowParseError; empty dicts allowed; unused groups produce SHOULD warnings (ADR_20260426_condition_inlining)
- Image generation deferred to v2 (ADR_20260426_image_rendering_deferral)

---

## Key Decisions

- Use `argparse` (stdlib) for CLI parsing — zero new dependencies (ADR_20260422_cli_parser_library)
- Read version from `importlib.metadata` at runtime — single source of truth, never hardcoded (ADR_20260422_version_source)
- Evidence type system: coerce all evidence values to strings; YAML booleans become lowercase, YAML numbers become numeric strings (ADR_20260426_evidence_type_system)
- Fuzzy match: ~= applies ONLY to numeric values with 5% tolerance; no string fuzzy matching (ADR_20260426_fuzzy_match_algorithm)
- Validation result: return ValidationResult with list of Violation objects (severity, message, location) — collect all violations at once (ADR_20260426_validation_result)
- CLI I/O convention: positional YAML path; --evidence/--evidence-json; 3-tier exit codes (0/1/2); stdout=results/stderr=errors; key-value text output (ADR_20260426_cli_io_convention)
- Subflow resolution: flow field is relative file path from root flow directory including extension; output as <flow-name>/<first-state-id> (ADR_20260426_subflow_resolution)
- Condition inlining: named references resolved at load time in the loader; three when forms (dict, list, string); unknown refs raise FlowParseError; empty dicts allowed; unused groups produce SHOULD warnings; GuardCondition unchanged; Transition gains referenced_condition_groups (ADR_20260426_condition_inlining)
- Image rendering: deferred to v2 — no Python-native Mermaid renderer without heavy deps (ADR_20260426_image_rendering_deferral)

---

## ADRs

See `docs/adr/` for the full decision record.

---

## Completed Features

See `docs/features/` for accepted features.

---

## Changes

| Date | Source | Change | Reason |
|------|--------|--------|--------|
| 2026-04-22 | ADR_20260422_cli_parser_library | Added CLI entrypoint with argparse | Feature cli-entrypoint |
| 2026-04-22 | ADR_20260422_version_source | Version read from importlib.metadata at runtime | Feature cli-entrypoint |
| 2026-04-26 | ADR_20260426_cli_io_convention | CLI I/O conventions established | Feature flowr-cli |
| 2026-04-26 | ADR_20260426_evidence_type_system | Evidence values coerced to strings | Feature flow-definition-spec |
| 2026-04-26 | ADR_20260426_fuzzy_match_algorithm | ~= operator restricted to numeric values only | Feature flow-definition-spec |
| 2026-04-26 | ADR_20260426_validation_result | ValidationResult with Violation list | Feature flow-definition-spec |
| 2026-04-26 | ADR_20260426_subflow_resolution | Subflow lookup by relative path | Feature flow-definition-spec |
| 2026-04-26 | ADR_20260426_condition_inlining | Named condition groups inlined at load time | Feature named-condition-groups |
| 2026-04-26 | ADR_20260426_image_rendering_deferral | Image generation deferred to v2 | Feature flow-definition-spec |