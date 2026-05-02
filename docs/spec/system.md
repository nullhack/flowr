# System Overview: flowr

> Current-state description of the production system.
> Updated by the Software Architect when domain understanding changes (rare).
> Contains only completed features — nothing from backlog or in-progress.
> This document captures what code cannot express: WHY contexts exist, HOW they relate, WHAT the aggregate boundaries are and why.

---

## Summary

flowr is a Python library and CLI for defining, validating, and visualizing non-deterministic state machine workflows in YAML. It provides a reference validator that checks flow definitions against the specification, a Mermaid converter that generates stateDiagram-v2 diagrams, a CLI with six subcommands (validate, states, check, next, transition, mermaid) for one-shot flow definition interaction, and a session management system that tracks workflow state across CLI invocations. Flow name resolution allows CLI arguments to accept short flow names (resolved from the configured flows directory) as well as file paths. Named condition groups allow flow authors to define reusable condition expressions at the state level and reference them by name in `when` clauses, eliminating repetition while remaining fully backwards compatible. The system uses Python dataclasses for its internal representation and PyYAML for parsing flow definition and session files.

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
| `Agent Operator` | AI agent running flowr commands in automated workflows, relying on session state to persist across invocations |

### Systems

| System | Kind | Description |
|--------|------|-------------|
| `flowr` | Internal | Python library for flow definition validation, conversion, session management, and CLI access |
| `YAML Source` | External | Flow definition files on disk that flowr loads and validates |
| `Session Store` | Internal | YAML files in `.flowr/sessions/` that persist workflow state across CLI invocations |

### Interactions

| Interaction | Behaviour | Technology |
|-------------|-----------|------------|
| Developer → flowr | Loads, validates, and converts flow definitions | Python API |
| Developer → flowr CLI | Runs `python -m flowr --help` / `--version` | CLI / subprocess |
| CLI User → flowr CLI | Runs subcommands on flow definition files | CLI / subprocess |
| Agent Operator → flowr CLI | Runs session-aware commands (`--session`) to track workflow state | CLI / subprocess |
| Tool Author → flowr | Builds validation and conversion tools on top of flowr | Python API |
| flowr → YAML Source | Reads flow definition files from disk | PyYAML |
| flowr → Session Store | Reads and writes session YAML files with atomic writes | PyYAML / stdlib |

---

## Container (C4 Level 2)

### Boundary: flowr

| Container | Technology | Responsibility |
|-----------|------------|----------------|
| CLI Entrypoint | Python / argparse | Parses subcommands and flags; resolves flow names; dispatches to domain operations; formats output; manages session-aware command mode |
| Flow Definition Domain | Python / dataclasses | Core domain types for flow definitions, states, transitions, conditions, params, and attrs |
| Session Domain | Python / dataclasses | Session and SessionStackFrame types for tracking workflow state across invocations |
| Validator | Python / dataclasses | Validates flow definitions against the specification; returns ValidationResult with Violations |
| Mermaid Converter | Python | Converts flow definitions to Mermaid stateDiagram-v2 format |
| Flow Loader | Python / PyYAML | Parses YAML files into Flow domain objects; resolves subflow references by relative path; inlines named condition groups at load time |
| Flow Name Resolver | Python / stdlib | Resolves short flow names to file paths using the configured flows directory; file paths take priority |
| Session Store | Python / PyYAML / stdlib | Persists session state to YAML files with atomic writes; loads sessions by name; lists sessions |

### Interactions

| Interaction | Behaviour |
|-------------|-----------|
| CLI User → CLI Entrypoint | Invokes via `flowr <subcommand>` or `python -m flowr <subcommand>` |
| Developer → CLI Entrypoint | Invokes via `python -m flowr` |
| Agent Operator → CLI Entrypoint | Invokes session-aware commands with `--session` flag |
| CLI Entrypoint → Flow Name Resolver | Resolves short flow names to file paths |
| CLI Entrypoint → Flow Loader | Loads root flow, resolves subflow references, and inlines named condition groups |
| CLI Entrypoint → Validator | Runs validate subcommand |
| CLI Entrypoint → Mermaid Converter | Runs mermaid subcommand |
| CLI Entrypoint → Session Store | Manages session state (init, show, set-state, list, transition updates) |
| Validator → Flow Definition Domain | Reads domain types to validate structure and semantics |
| Mermaid Converter → Flow Definition Domain | Reads domain types to generate diagram output |
| Flow Loader → YAML Source | Reads YAML files from disk |
| Session Store → Session Store (disk) | Atomic writes (temp-file-then-rename) to `.flowr/sessions/` |

---

## Module Structure

| Module | Responsibility | Bounded Context |
|--------|----------------|-----------------|
| `flowr/__main__.py` | CLI entrypoint: builds argparse parser with subcommands and global flags (`--flows-dir`); resolves flow names; dispatches; formats output; session-aware command mode; exit codes | CLI |
| `flowr/__init__.py` | Package marker; no public API | CLI |
| `flowr/cli/__init__.py` | CLI subpackage marker | CLI |
| `flowr/cli/output.py` | Output formatting: text and JSON formatters for CLI results | CLI |
| `flowr/cli/resolution.py` | Flow name resolution: FlowNameResolver Protocol, DefaultFlowNameResolver, FlowNameNotFound exception | CLI |
| `flowr/cli/session_cmd.py` | Session subcommand group: init, show, set-state, list — parses args, dispatches to SessionStore, formats output | CLI |
| `flowr/domain/__init__.py` | Domain subpackage marker | Flow Definition |
| `flowr/domain/flow_definition.py` | Core domain types: Flow, State, Transition, GuardCondition, ConditionExpression, Param; State carries optional named condition groups; Transition tracks referenced condition groups | Flow Definition |
| `flowr/domain/validation.py` | Validation types: ConformanceLevel, Violation, ValidationResult; validate function; condition reference and unused group checks | Flow Definition |
| `flowr/domain/condition.py` | Condition evaluation: ConditionOperator enum, evaluate_condition function | Flow Definition |
| `flowr/domain/mermaid.py` | Mermaid stateDiagram-v2 conversion: to_mermaid function; shows resolved conditions on transition labels | Flow Definition |
| `flowr/domain/session.py` | Session types: Session, SessionStackFrame dataclasses; SessionStore Protocol for persistence interface | Session Tracking |
| `flowr/domain/loader.py` | YAML parsing Protocol and load_flow function; subflow resolution; condition inlining via resolve_when_clause | Flow Definition |
| `flowr/infrastructure/__init__.py` | Infrastructure subpackage marker | Infrastructure |
| `flowr/infrastructure/config.py` | Configuration resolution: FlowrConfig dataclass, resolve_config function; reads `[tool.flowr]` from `pyproject.toml` with CLI overrides | CLI |
| `flowr/infrastructure/session_store.py` | Session persistence: YamlSessionStore implements SessionStore Protocol; atomic writes via temp-file-then-rename; loads/lists sessions from `.flowr/sessions/` | Session Tracking |

---

## Domain Model Documentation

### Why Each Context Exists

| Bounded Context | Business Capability | Why It's Separate |
|-----------------|---------------------|-------------------|
| `CLI` | Expose the application as a command-line tool with subcommands; parse args; resolve flow names; format and display results; manage session-aware command mode | The CLI is a delivery mechanism — a driving adapter — that depends on the domain. It has no business logic of its own and can be replaced without touching the domain. |
| `Flow Definition` | Define, validate, and convert non-deterministic state machine workflows in YAML | This is the core domain — the reason the product exists. It owns all domain types and invariants. Separating it from CLI ensures the domain is testable and reusable without the CLI layer. |
| `Session Tracking` | Manage persistent workflow state across CLI invocations; track subflow push/pop stack; provide session-aware command mode | Session Tracking has its own persistence (YAML files), lifecycle (init, show, set-state, list), and invariants (atomic writes, stack consistency). It conforms to Flow Definition's vocabulary (flow names, state IDs) but owns its own storage and consistency boundaries. |

### Aggregate Boundary Rationale

| Aggregate | Why These Entities Are Grouped | Transactional Invariant |
|-----------|-------------------------------|------------------------|
| Flow | A Flow is the root entity of a flow definition; all States, Transitions, and Conditions belong to a single Flow and are loaded and validated together | A Flow must be self-consistent: all next targets resolve to valid states or exits, no cross-flow cycles exist, and all condition references resolve |
| Session | A Session tracks workflow state across CLI invocations; it has its own persistence (YAML files) and a subflow call stack that must remain LIFO-consistent | A Session's (flow, state) pair must reference a valid state within a loaded flow; the subflow stack must be LIFO-consistent after every push/pop; session writes must be atomic (temp-file-then-rename) |

---

## Active Constraints

- PyYAML is the only runtime dependency — all flow definition and session parsing uses `yaml.safe_load`
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
- Flow name resolution: file paths take priority over name resolution; only `.yaml` extension is tried; case-sensitive matching (Technical Design)
- Session writes use atomic write (temp-file-then-rename) to prevent partial corruption (Technical Design)
- Session-aware commands are opt-in via `--session` flag; commands without `--session` behave identically to the pre-session version (Technical Design)
- No concurrency control for session files; last-write-wins is acceptable for single-user CLI usage (Technical Design)
- `session init` does not accept params; the `params` field is reserved for future use (Technical Design)

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
- Flow name resolution: file paths take priority; only `.yaml` extension tried; case-sensitive; `--flows-dir` global flag overrides config (Technical Design)
- Session persistence: atomic writes via temp-file-then-rename; YAML format; no concurrency control (last-write-wins) (Technical Design)
- Session-aware commands: `--session` flag on next/transition/check; `session` subcommand group (init, show, set-state, list); backward compatible (Technical Design)
- Hexagonal architecture: CLI as primary adapter, domain as core, infrastructure as secondary adapter; SessionStore as Protocol in domain, YamlSessionStore as infrastructure implementation (Technical Design)

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
| 2026-05-01 | Technical Design | Added Session Tracking bounded context; updated CLI context with flow name resolution and session-aware commands; added SessionStore Protocol and YamlSessionStore; updated module structure with new modules (resolution.py, session_cmd.py, session_store.py); updated aggregate boundary for Session; added Agent Operator actor; added Session Store system | Features cli-flow-name-resolution, session-management |