# System Overview: flowr

> Current-state description of the production system.
> Rewritten by the system-architect at Step 2 for each feature cycle.
> Contains only completed features — nothing from backlog or in-progress.

---

## Summary

flowr is a Python library and CLI for defining, validating, and visualizing non-deterministic state machine
workflows in YAML. It provides a reference validator that checks flow definitions against the
specification, a Mermaid converter that generates stateDiagram-v2 diagrams, and a CLI with six
subcommands (validate, states, check, next, transition, mermaid) for one-shot flow definition
interaction. Named condition groups allow flow authors to define reusable condition expressions at the
state level and reference them by name in `when` clauses, eliminating repetition while remaining fully
backwards compatible. The system uses Python dataclasses for its internal representation and PyYAML for
parsing flow definition files.

---

## Context

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

## Container

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

## Structure

| Module | Responsibility |
|--------|----------------|
| `flowr/__main__.py` | CLI entrypoint: builds argparse parser with subcommands; dispatches; formats output; exit codes |
| `flowr/__init__.py` | Package marker; no public API |
| `flowr/cli/__init__.py` | CLI subpackage marker |
| `flowr/cli/output.py` | Output formatting: text and JSON formatters for CLI results |
| `flowr/domain/__init__.py` | Domain subpackage marker |
| `flowr/domain/flow_definition.py` | Core domain types: Flow, State, Transition, GuardCondition, ConditionExpression, Param; State carries optional named condition groups; Transition tracks referenced condition groups |
| `flowr/domain/validation.py` | Validation types: ConformanceLevel, Violation, ValidationResult; validate function; condition reference and unused group checks |
| `flowr/domain/condition.py` | Condition evaluation: ConditionOperator enum, evaluate_condition function |
| `flowr/domain/mermaid.py` | Mermaid stateDiagram-v2 conversion: to_mermaid function; shows resolved conditions on transition labels |
| `flowr/domain/session.py` | Session format: Session, SessionStack types |
| `flowr/domain/loader.py` | YAML parsing Protocol and load_flow function; subflow resolution; condition inlining via resolve_when_clause |
| `flowr/cli/output.py` | Output formatting: text and JSON formatters for CLI results |

---

## Domain Model

### Bounded Contexts

| Context | Responsibility | Key Modules |
|---------|----------------|-------------|
| `CLI` | Expose the application as a command-line tool with 6 subcommands; parse args; format and display results | `flowr/__main__.py`, `flowr/cli/output.py` |
| `Flow Definition` | Define, validate, and convert non-deterministic state machine workflows in YAML | `flowr/domain/` |

### Entities

| Name | Type | Description | Bounded Context |
|------|------|-------------|-----------------|
| `Flow` | Entity | Top-level YAML document describing a workflow with flow name, version, params, exits, attrs, and states | Flow Definition |
| `State` | Value Object | A node in the workflow with an id, transitions, optional subflow reference, optional attrs, and optional named condition groups | Flow Definition |
| `Transition` | Value Object | A trigger-to-target mapping; simple (string target) or guarded (with when conditions); tracks referenced condition groups for validation | Flow Definition |
| `GuardCondition` | Value Object | A when clause mapping evidence keys to condition expression strings | Flow Definition |
| `ConditionExpression` | Value Object | An operator and value string (e.g., >=80%) for transition guard evaluation | Flow Definition |
| `ConditionOperator` | Enum | ==, !=, >=, <=, >, <, ~= — the seven condition operators | Flow Definition |
| `Param` | Value Object | A parameter declaration with a name and optional default value | Flow Definition |
| `ConformanceLevel` | Enum | MUST (required) or SHOULD (recommended) — severity levels for validation violations | Flow Definition |
| `Violation` | Value Object | A validation finding with severity, message, and location within a flow definition | Flow Definition |
| `ValidationResult` | Value Object | The result of validating a flow definition; contains a list of Violations with convenience methods | Flow Definition |
| `Session` | Value Object | Minimal session tracking: current flow, state, and call stack | Flow Definition |
| `SessionStack` | Value Object | Stack of (flow, state) pairs tracking subflow nesting depth | Flow Definition |
| `CLIRunner` | Service | Orchestrates CLI subcommand execution: parse args, load flows, invoke domain operations, format output | CLI |
| `OutputFormatter` | Service | Formats domain results as human-readable text or JSON for CLI output | CLI |

### Actions

| Name | Actor | Object | Description |
|------|-------|--------|-------------|
| `validate` | Validator | Flow → ValidationResult | Validates a flow definition against all specification rules; collects MUST errors and SHOULD warnings |
| `resolve_target` | Validator | next target → State or Exit | Resolves a next target to a state id or exit name; rejects ambiguous or unresolvable targets |
| `evaluate_condition` | Validator | ConditionExpression × Evidence → bool | Evaluates a condition expression against evidence values; coerces evidence to strings, applies numeric extraction |
| `check_cycles` | Validator | [FlowDefinition] → [Violation] | Checks for cross-flow cycles via DFS; within-flow cycles are allowed |
| `check_condition_references` | Validator | Flow → [Violation] | Checks that all named condition references in when clauses resolve to a key in the same state's conditions block; MUST error for unknown refs |
| `check_unused_condition_groups` | Validator | Flow → [Violation] | Checks that all defined condition groups are referenced by at least one transition; SHOULD warning for unused groups |
| `to_mermaid` | Converter | Flow → str | Converts a flow definition to a Mermaid stateDiagram-v2 string; shows resolved conditions on transition labels |
| `load_flow` | Loader | YAML string → Flow | Parses a YAML document into a Flow domain object |
| `load_flow_from_file` | Loader | file path → Flow | Loads a flow definition from a YAML file on disk |
| `resolve_subflows` | Loader | Flow → list[Flow] | Recursively resolves subflow references by relative path from root flow directory |
| `resolve_when_clause` | Loader | when clause × conditions × state_id → (GuardCondition, frozenset[str] | None) | Resolves named condition references in a when clause into a flat condition dict; raises FlowParseError for unknown references |
| `format_text` | OutputFormatter | result → str | Formats a CLI result as human-readable key-value text |
| `format_json` | OutputFormatter | result → str | Formats a CLI result as JSON |
| `run_validate` | CLIRunner | file path → exit code + output | Runs the validate subcommand |
| `run_states` | CLIRunner | file path → exit code + output | Runs the states subcommand |
| `run_check` | CLIRunner | file path + state [+ target] → exit code + output | Runs the check subcommand |
| `run_next` | CLIRunner | file path + state + evidence → exit code + output | Runs the next subcommand |
| `run_transition` | CLIRunner | file path + state + trigger + evidence → exit code + output | Runs the transition subcommand |
| `run_mermaid` | CLIRunner | file path → exit code + output | Runs the mermaid subcommand |

### Relationships

| Subject | Relation | Object | Cardinality | Notes |
|---------|----------|--------|-------------|-------|
| `Flow` | contains | `State` | 1:N | Ordered list; first state is initial |
| `Flow` | declares | `Param` | 0:N | Optional parameter declarations |
| `Flow` | declares | `Exit` | 1:N | Exits are always required |
| `State` | contains | `Transition` | 1:N | Trigger-to-target mapping |
| `Transition` | may have | `GuardCondition` | 0:1 | Simple transitions have no guard |
| `Transition` | may reference | `ConditionGroup` | 0:N | Via referenced_condition_groups; tracks which named groups were inlined |
| `State` | may define | `ConditionGroup` | 0:N | Via conditions field; named groups scoped to their defining state |
| `GuardCondition` | contains | `ConditionExpression` | 1:N | AND-combined conditions |
| `ValidationResult` | contains | `Violation` | 0:N | All violations collected at once |
| `Session` | contains | `SessionStack` | 0:1 | Stack present when inside a subflow |
| `State` | may invoke | `Flow` | 0:1 | Via the flow field for subflows |
| `CLIRunner` | uses | `Flow Loader` | 1:1 | Loads flows for subcommand execution |
| `CLIRunner` | uses | `OutputFormatter` | 1:1 | Formats results for display |
| `CLIRunner` | uses | `Validator` | 1:1 | For validate subcommand |
| `CLIRunner` | uses | `Mermaid Converter` | 1:1 | For mermaid subcommand |

### Module Dependencies

| Module | Depends On |
|--------|------------|
| `flowr/__main__.py` | `argparse` (stdlib), `importlib.metadata` (stdlib), `flowr/cli/output.py`, `flowr/domain/` |
| `flowr/cli/__init__.py` | — |
| `flowr/cli/output.py` | `json` (stdlib), `flowr/domain/` |
| `flowr/domain/flow_definition.py` | `dataclasses` (stdlib), `typing` (stdlib) |
| `flowr/domain/validation.py` | `flowr/domain/flow_definition.py`, `enum` (stdlib) |
| `flowr/domain/condition.py` | `flowr/domain/flow_definition.py`, `enum` (stdlib), `re` (stdlib) |
| `flowr/domain/mermaid.py` | `flowr/domain/flow_definition.py` |
| `flowr/domain/session.py` | `dataclasses` (stdlib), `typing` (stdlib) |
| `flowr/domain/loader.py` | `flowr/domain/flow_definition.py`, `typing` (stdlib), `pathlib` (stdlib), `yaml` (PyYAML) |

---

## Active Constraints

- PyYAML is the only runtime dependency — all flow definition parsing uses `yaml.safe_load`
- All evidence values are coerced to strings before condition evaluation (ADR-2026-04-26-evidence-type-system)
- The ~= operator applies ONLY to numeric values (5% tolerance); no string fuzzy matching (ADR-2026-04-26-fuzzy-match-algorithm)
- Validator returns ValidationResult with Violation list — no exceptions for validation failures (ADR-2026-04-26-validation-result)
- Version format is calver (`major.minor.YYYYMMDD`); tests must not assume semver
- CLI exit codes: 0 = success, 1 = command failed, 2 = usage error (ADR-2026-04-26-cli-io-convention)
- CLI output: stdout for results, stderr for errors/warnings (ADR-2026-04-26-cli-io-convention)
- Evidence input: `--evidence key=value` for simple, `--evidence-json` for complex (ADR-2026-04-26-cli-io-convention)
- Subflow lookup: `flow` field is relative file path from root flow directory, including extension (ADR-2026-04-26-subflow-resolution)
- Named condition groups are inlined at load time; after resolution, GuardCondition remains a flat dict; unknown refs raise FlowParseError; empty dicts allowed; unused groups produce SHOULD warnings (ADR-2026-04-26-condition-inlining)
- Image generation deferred to v2 (ADR-2026-04-26-image-rendering-deferral)

---

## Key Decisions

- Use `argparse` (stdlib) for CLI parsing — zero new dependencies (ADR-2026-04-22-cli-parser-library)
- Read version from `importlib.metadata` at runtime — single source of truth, never hardcoded (ADR-2026-04-22-version-source)
- Evidence type system: coerce all evidence values to strings; YAML booleans become lowercase, YAML numbers become numeric strings (ADR-2026-04-26-evidence-type-system)
- Fuzzy match: ~= applies ONLY to numeric values with 5% tolerance; no string fuzzy matching (ADR-2026-04-26-fuzzy-match-algorithm)
- Validation result: return ValidationResult with list of Violation objects (severity, message, location) — collect all violations at once (ADR-2026-04-26-validation-result)
- CLI I/O convention: positional YAML path; --evidence/--evidence-json; 3-tier exit codes (0/1/2); stdout=results/stderr=errors; key-value text output (ADR-2026-04-26-cli-io-convention)
- Subflow resolution: flow field is relative file path from root flow directory including extension; output as <flow-name>/<first-state-id> (ADR-2026-04-26-subflow-resolution)
- Condition inlining: named references resolved at load time in the loader; three when forms (dict, list, string); unknown refs raise FlowParseError; empty dicts allowed; unused groups produce SHOULD warnings; GuardCondition unchanged; Transition gains referenced_condition_groups (ADR-2026-04-26-condition-inlining)
- Image rendering: deferred to v2 — no Python-native Mermaid renderer without heavy deps (ADR-2026-04-26-image-rendering-deferral)

---

## ADRs

See `docs/adr/` for the full decision record.

---

## Configuration Keys

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `project.name` | string | `"flowr"` | Application name; read from installed package metadata |
| `project.description` | string | `"non-deterministic state machine specification to knead workflows"` | Package description from `pyproject.toml`; set as `argparse` description |
| `project.version` | string | `"0.1"` | Version; read at runtime via `importlib.metadata` |

---

## External Dependencies

| Dependency | What it provides | Why not replaced |
|------------|------------------|-----------------|
| `argparse` | CLI argument parsing | stdlib; zero install cost; sufficient for 2-flag skeleton |
| `importlib.metadata` | Runtime package metadata access | stdlib; canonical API since Python 3.8 |
| `PyYAML` | YAML parsing for flow definition files | De facto standard for YAML in Python; no viable stdlib alternative |

---

## Completed Features

See `docs/features/completed/` for accepted features.