# Technical Design: flowr

> Architecture and implementation design for the cli-flow-name-resolution and session-management features.
> Authored by the System Architect during the technical-design state.

---

## Architectural Style

**Hexagonal Architecture (Ports & Adapters)**

The system follows a hexagonal architecture with three layers:

| Layer | Role | Dependency Direction |
|-------|------|---------------------|
| **Primary Adapter (CLI)** | Driving adapter — parses args, resolves names, dispatches commands, formats output | Depends inward on domain |
| **Domain Core** | Business logic — flow definitions, sessions, validation, conditions | Depends on nothing |
| **Secondary Adapter (Infrastructure)** | Driven adapter — file I/O, config resolution, session persistence | Depends inward on domain |

New modules follow this same pattern: `flowr/cli/` for primary adapters, `flowr/domain/` for core logic, `flowr/infrastructure/` for secondary adapters.

---

## Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.12+ | Project requirement; dataclasses with slots, Protocol, tomllib |
| CLI | argparse (stdlib) | Existing ADR_20260422_cli_parser_library — zero new dependencies |
| YAML parsing | PyYAML | Existing runtime dependency for flow and session files |
| Domain types | dataclasses (frozen, slots) | Existing pattern — immutable value objects and entities |
| Config | tomllib (stdlib) | Existing pattern — reads `[tool.flowr]` from `pyproject.toml` |
| Session persistence | stdlib (`pathlib`, `os.replace`, `tempfile`) | Atomic write via temp-file-then-rename — no new dependencies |

**No new runtime dependencies are introduced.**

---

## Module Structure

### New Modules

| Module | Responsibility | Bounded Context |
|--------|----------------|-----------------|
| `flowr/cli/resolution.py` | Flow name resolution: maps short flow names to file paths using configured `flows_dir`; file paths take priority | CLI |
| `flowr/cli/session_cmd.py` | Session subcommand group: `init`, `show`, `set-state`, `list` — parses args, dispatches to domain/infrastructure, formats output | CLI |
| `flowr/infrastructure/session_store.py` | Session persistence: load/save session YAML files with atomic writes; implements `SessionStore` protocol | Session Tracking (infrastructure adapter) |

### Modified Modules

| Module | Change | Bounded Context |
|--------|--------|-----------------|
| `flowr/__main__.py` | Add `--flows-dir` global flag; add `--session` flag to `next`, `transition`, `check`; add `--format` flag to session commands; add `session` subcommand group; integrate `FlowNameResolver` for flow argument resolution; integrate session-aware command dispatch | CLI |
| `flowr/domain/session.py` | Add `SessionStore` Protocol class; add `FlowNameResolver` Protocol class (or place in `flowr/cli/resolution.py` — see Interface Definitions) | Session Tracking / CLI |
| `flowr/infrastructure/config.py` | No structural changes — `FlowrConfig` already has `flows_dir`, `sessions_dir`, `default_flow`, `default_session` fields | CLI |

### Unchanged Modules

| Module | Responsibility |
|--------|----------------|
| `flowr/domain/flow_definition.py` | Core domain types — unchanged |
| `flowr/domain/validation.py` | Validation — unchanged |
| `flowr/domain/condition.py` | Condition evaluation — unchanged |
| `flowr/domain/mermaid.py` | Mermaid conversion — unchanged |
| `flowr/domain/loader.py` | YAML parsing — unchanged |
| `flowr/cli/output.py` | Output formatting — unchanged (reused by session commands) |

---

## Interface Definitions

### FlowNameResolver Protocol

```python
# flowr/cli/resolution.py

class FlowNameResolver(Protocol):
    """Resolve a flow name or file path to a valid flow file path.

    If the argument is an existing file path, return it directly.
    Otherwise, treat it as a flow name and search the configured
    flows directory for a matching .yaml file.
    """

    def resolve(self, flow_arg: str, flows_dir: Path) -> Path:
        """Resolve a flow argument to a file path.

        Args:
            flow_arg: A file path or short flow name.
            flows_dir: The configured flows directory.

        Returns:
            The resolved Path to the flow YAML file.

        Raises:
            FlowNameNotFound: The argument is not an existing file
                and no matching .yaml file exists in flows_dir.
        """
        ...
```

### DefaultFlowNameResolver

```python
# flowr/cli/resolution.py

class DefaultFlowNameResolver:
    """Default implementation: file paths first, then name resolution."""

    def resolve(self, flow_arg: str, flows_dir: Path) -> Path:
        path = Path(flow_arg)
        if path.exists():
            return path
        # Try <flows_dir>/<flow_arg>.yaml
        candidate = flows_dir / f"{flow_arg}.yaml"
        if candidate.exists():
            return candidate
        raise FlowNameNotFound(
            f"Flow '{flow_arg}' not found in {flows_dir}"
        )
```

### FlowNameNotFound Exception

```python
# flowr/cli/resolution.py

class FlowNameNotFound(Exception):
    """Raised when a flow name cannot be resolved to a file path."""
```

### SessionStore Protocol

```python
# flowr/domain/session.py (added to existing module)

class SessionStore(Protocol):
    """Persistence interface for session state.

    Implementations must use atomic writes (temp-file-then-rename)
    to prevent partial state corruption.
    """

    def init(self, flow_name: str, name: str, flows_dir: Path) -> Session:
        """Create a new session at the flow's initial state.

        Args:
            flow_name: The flow name (resolved via FlowNameResolver).
            name: The session name (used as filename stem).
            flows_dir: The configured flows directory (for loading the flow).

        Returns:
            The newly created Session.

        Raises:
            SessionAlreadyExists: A session with this name already exists.
            FlowNotFound: The flow name cannot be resolved.
        """
        ...

    def load(self, session_arg: str) -> Session:
        """Load a session by name or file path.

        If session_arg is an existing file path, load it directly.
        Otherwise, resolve it as <sessions_dir>/<session_arg>.yaml.

        Args:
            session_arg: A session name or file path.

        Returns:
            The loaded Session.

        Raises:
            SessionNotFound: No session file exists for this name.
            SessionNameNotFoundError: The argument is not an existing file
                and no matching .yaml file exists in sessions_dir.
        """
        ...

    def save(self, session: Session) -> None:
        """Persist a session using atomic write.

        Args:
            session: The session to save.
        """
        ...

    def list_sessions(self) -> list[Session]:
        """List all sessions in the session store.

        Returns:
            List of all sessions, sorted by updated_at descending.
        """
        ...
```

### YamlSessionStore Implementation

```python
# flowr/infrastructure/session_store.py

class YamlSessionStore:
    """File-based session store using YAML with atomic writes.

    Sessions are stored as <name>.yaml in the configured sessions directory.
    Writes use temp-file-then-rename to prevent partial corruption.
    """

    def __init__(self, sessions_dir: Path) -> None:
        self._sessions_dir = sessions_dir

    def init(self, flow_name: str, name: str, flows_dir: Path) -> Session:
        """Create a new session at the flow's initial state."""
        ...

    def load(self, name: str) -> Session:
        """Load a session from its YAML file."""
        ...

    def save(self, session: Session) -> None:
        """Save a session using atomic write (write temp, then rename)."""
        ...

    def list_sessions(self) -> list[Session]:
        """List all sessions, sorted by updated_at descending."""
        ...
```

---

## API Contracts

### Global Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--flows-dir` | `str` | From `[tool.flowr].flows_dir` in `pyproject.toml`, default `.flowr/flows` | Override the flows directory for this invocation |

### Session Subcommand Group

```
flowr session <subcommand> [options]
```

#### `flowr session init <flow> [--name <name>]`

| Field | Value |
|-------|-------|
| **Purpose** | Create a new session at the flow's initial state |
| **Positional** | `flow` — flow name or file path (resolved via FlowNameResolver) |
| **Options** | `--name` — session name or file path (default: from `[tool.flowr].default_session`, default `default`) |

#### `flowr session show [--name <name-or-path>] [--format yaml\|json]`

| Field | Value |
|-------|-------|
| **Purpose** | Display the current session's flow, state, stack, and attrs |
| **Options** | `--name` — session name or file path (default: from config `default_session`) |
| **Options** | `--format` — output format: `yaml` (default) or `json` |
| **Output** | Session state: flow, state, stack, attrs, created_at, updated_at |
| **Exit codes** | 0 = success, 1 = session not found, 2 = usage error |

#### `flowr session set-state <state> [--name <name>]`

| Field | Value |
|-------|-------|
| **Purpose** | Update the current state in a session |
| **Positional** | `state` — the new state ID |
| **Options** | `--name` — session name or file path (default: from config `default_session`) |
| **Output** | Updated session state: flow, state, updated_at |
| **Exit codes** | 0 = success, 1 = state not found in flow or session not found, 2 = usage error |

#### `flowr session list [--format yaml\|json]`

| Field | Value |
|-------|-------|
| **Purpose** | List all sessions in the session store |
| **Options** | `--format` — output format: `yaml` (default) or `json` |
| **Output** | List of sessions with name, flow, state, updated_at |
| **Exit codes** | 0 = success, 2 = usage error |

### Session-Aware Flags on Existing Commands

#### `flowr next <flow_or_state> [--session [<name>]] [--evidence ...]`

When `--session` is provided:
- The `flow_file` positional argument is no longer required — the flow is read from the session
- The `state_id` positional argument is no longer required — the state is read from the session
- If `--session` is given without a value, the default session name from config is used
- `--session` accepts a session name or file path
- After computing the result, the session file is NOT updated (next is read-only)

When `--session` is not provided, behavior is identical to the current version.

#### `flowr transition <flow_or_state> <trigger> [--session [<name>]] [--evidence ...]`

When `--session` is provided:
- The `flow_file` positional argument is no longer required — the flow is read from the session
- The `state_id` positional argument is no longer required — the state is read from the session
- If `--session` is given without a value, the default session name from config is used
- `--session` accepts a session name or file path
- After a successful transition, the session file IS auto-updated with the new state
- If the transition enters a subflow, the parent flow+state is pushed onto the session stack
- If the transition exits a subflow, the parent flow+state is popped from the session stack

When `--session` is not provided, behavior is identical to the current version.

#### `flowr check <flow_or_state> [target] [--session [<name>]]`

When `--session` is provided:
- The `flow_file` positional argument is no longer required — the flow is read from the session
- The `state_id` positional argument is no longer required — the state is read from the session
- If `--session` is given without a value, the default session name from config is used
- `--session` accepts a session name or file path
- The session file is NOT updated (check is read-only)

When `--session` is not provided, behavior is identical to the current version.

### Flow Name Resolution

The `flow_file` positional argument on all existing subcommands (validate, states, check, next, transition, mermaid) is replaced by a `flow` positional argument that accepts either a file path or a short flow name. Resolution logic:

1. If the argument is an existing file path → use it directly
2. Otherwise → treat as a flow name, append `.yaml`, search in the configured `flows_dir`
3. If not found → error with the flow name and searched directory

This applies to all subcommands that currently take a `flow_file` positional argument.

---

## Configuration

### Existing Configuration Keys (unchanged)

| Key | Type | Default | Source |
|-----|------|---------|--------|
| `flows_dir` | `Path` | `.flowr/flows` | `[tool.flowr]` in `pyproject.toml` |
| `sessions_dir` | `Path` | `.flowr/sessions` | `[tool.flowr]` in `pyproject.toml` |
| `default_flow` | `str` | `main-flow` | `[tool.flowr]` in `pyproject.toml` |
| `default_session` | `str` | `default` | `[tool.flowr]` in `pyproject.toml` |

### New CLI Flags

| Flag | Maps To | Overrides |
|------|---------|-----------|
| `--flows-dir <path>` | `cli_overrides["flows_dir"]` | `[tool.flowr].flows_dir` |

The `FlowrConfig` dataclass already has all required fields. The `--flows-dir` flag is the only new global flag. Session name defaults use the existing `default_session` config key.

---

## Deferred Decisions (Resolved)

### Q8: Extension Resolution Strategy (cli-flow-name-resolution)

**Decision:** Only `.yaml` extension is tried. Flow names are resolved as `<flows_dir>/<name>.yaml`. No fallback to `.yml`.

**Rationale:** The project convention is `.yaml` (all existing flow files use `.yaml`). Supporting multiple extensions adds complexity with no clear benefit. If a user has `.yml` files, they can pass the full file path.

### Q10: Corrupted Session File Recovery (session-management)

**Decision:** If a session YAML file cannot be parsed, the CLI reports a clear error identifying the session name and the parse failure. No automatic recovery or repair is attempted. The user can delete or manually fix the session file.

**Rationale:** Session files are small, human-readable YAML. Automatic repair risks data loss. A clear error message lets the user decide how to proceed.

### Q11: Params on Session Init (session-management)

**Decision:** `session init` does NOT accept params. The `params` field in the Session dataclass is reserved for future use. Sessions are initialized with an empty `params` dict.

**Rationale:** No current use case requires param passing at init time. YAGNI — add params when a concrete requirement emerges.

### Q13: Concurrent Session Access (session-management)

**Decision:** Last-write-wins with atomic writes. No file locking or concurrency control.

**Rationale:** flowr is a single-user CLI tool. Concurrent access is out of scope (see product definition). Atomic writes prevent partial corruption; last-write-wins is acceptable for the intended use case.

---

## Data Flow

### Flow Name Resolution

```
CLI arg (flow name or path)
    │
    ▼
FlowNameResolver.resolve()
    │
    ├── Path exists? → return Path
    │
    └── flows_dir/<name>.yaml exists? → return Path
        │
        └── Not found → raise FlowNameNotFound
```

### Session Init

```
flowr session init <flow> [--name <name>]
    │
    ▼
FlowNameResolver.resolve(flow, flows_dir) → flow_path
    │
    ▼
load_flow_from_file(flow_path) → Flow
    │
    ▼
SessionStore.init(flow_name=flow.flow, name=name, flows_dir=flows_dir)
    │
    ├── Check session doesn't already exist
    │
    ├── Create Session(flow=flow.flow, state=flow.states[0].id, name=name)
    │
    └── Atomic write to <sessions_dir>/<name>.yaml
```

### Session-Aware Transition

```
flowr transition <trigger> --session [<name>] [--evidence ...]
    │
    ▼
SessionStore.load(name) → Session
    │
    ▼
FlowNameResolver.resolve(session.flow, flows_dir) → flow_path
    │
    ▼
load_flow_from_file(flow_path) → Flow
    │
    ▼
Find state in flow → validate trigger + evidence
    │
    ├── Transition enters subflow?
    │   → Session.push_stack(frame, new_state)
    │   → SessionStore.save(updated_session)
    │
    ├── Transition exits subflow?
    │   → Session.pop_stack(new_state)
    │   → SessionStore.save(updated_session)
    │
    └── Normal transition?
        → Session.with_state(new_state)
        → SessionStore.save(updated_session)
```

### Session List

```
flowr session list [--format yaml|json]
    │
    ▼
SessionStore.list_sessions() → list[Session]
    │
    ▼
Format and output
```

---

## Session YAML Format

Session files are stored in `<sessions_dir>/<name>.yaml`:

```yaml
flow: feature-development-flow
state: step-2-design
name: default
created_at: "2026-05-01T10:30:00"
updated_at: "2026-05-01T14:22:00"
stack: []
params: {}
```

With a subflow stack entry:

```yaml
flow: scope-cycle
state: step-1-scope
name: default
created_at: "2026-05-01T10:30:00"
updated_at: "2026-05-01T14:25:00"
stack:
  - flow: feature-development-flow
    state: step-1-scope
params: {}
```

---

## Error Handling

| Error | Exit Code | stderr Message | Condition |
|-------|-----------|----------------|-----------|
| `FlowNameNotFound` | 1 | `error: Flow '<name>' not found in <flows_dir>` | Flow name not resolved |
| `SessionNotFound` | 1 | `error: Session '<name>' not found` | Session file doesn't exist |
| `SessionAlreadyExists` | 1 | `error: Session '<name>' already exists` | Init on existing session |
| `StateNotFound` | 1 | `error: State '<state>' not found in flow '<flow>'` | Invalid state ID |
| `SessionCorrupted` | 1 | `error: Session '<name>' is corrupted: <detail>` | YAML parse failure |
| `FlowParseError` | 1 | `error: invalid flow definition: <detail>` | Existing — unchanged |
| Usage error | 2 | argparse default | Invalid args |

---

## Backward Compatibility

All existing CLI commands work identically when `--session` is not provided:

- `flowr validate <flow>` — unchanged (flow arg now accepts names too)
- `flowr states <flow>` — unchanged
- `flowr check <flow> <state>` — unchanged
- `flowr next <flow> <state>` — unchanged
- `flowr transition <flow> <state> <trigger>` — unchanged
- `flowr mermaid <flow>` — unchanged

The `flow_file` positional argument is renamed to `flow` internally but accepts the same file paths as before, plus short flow names as a new capability.

---

## Dependencies

| Dependency | Version | Type | Used By |
|------------|---------|------|---------|
| Python | ≥3.12 | Runtime | All modules |
| PyYAML | existing | Runtime | Session YAML read/write, flow loading |
| argparse | stdlib | Runtime | CLI parsing |
| tomllib | stdlib (3.11+) | Runtime | Config resolution |
| dataclasses | stdlib | Runtime | Domain types |

**No new runtime dependencies are introduced.**

---

## Changes

| Date | Source | Change | Reason |
|------|--------|--------|--------|
| 2026-05-01 | Technical Design | Initial technical design for cli-flow-name-resolution and session-management features | Architecture flow — technical-design state |