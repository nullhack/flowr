<div align="center">

<img src="https://raw.githubusercontent.com/nullhack/flowr/main/docs/assets/banner.svg" alt="flowr — non-deterministic state machine specification to knead workflows" width="100%"/>

<br/><br/>

[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?style=for-the-badge)](https://nullhack.github.io/flowr/coverage/)
[![CI](https://img.shields.io/github/actions/workflow/status/nullhack/flowr/ci.yml?style=for-the-badge&label=CI)](https://github.com/nullhack/flowr/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-%E2%89%A53.13-blue?style=for-the-badge)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/flowr?color=%2300FF41&style=for-the-badge)](https://pypi.org/project/flowr/)
[![MIT License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](https://github.com/nullhack/flowr/blob/main/LICENSE)

**A declarative, validatable YAML format for non-deterministic state machine workflows.**

[Read the specification →](https://nullhack.github.io/flowr/)

</div>

---

## The specification

flowr defines what a workflow **is** — its states, transitions, guard conditions, subflows — not what it **does**. No execution engine. No side effects. No opinions about retries, timeouts, or error handling. A YAML file declares structure. A validator checks integrity. Tools query, track, and visualise. [The format is the foundation.](https://nullhack.github.io/flowr/)

What the specification covers:

- **States** with unique ids, per-state attributes, and transition mappings
- **Transitions** that resolve to state ids or declared exit names
- **Guard conditions** gated by evidence-based expressions using 6 operators (`==`, `!=`, `>=`, `<=`, `>`, `<`)
- **Named condition groups** reusable across transitions on the same state
- **Subflows** with call-stack semantics — push on entry, pop on exit
- **Within-flow cycles** for iterative workflows
- **Validation rules** — structural integrity checks independent of any runtime

What the specification does **not** cover:

- Execution engines, side-effect hooks, retry logic, timeout handling
- Parallel (fork-join) states
- Orchestration, scheduling, or event dispatch

Existing solutions (BPMN, SCXML, Serverless Workflow, XState, Temporal) target execution or are framework-specific. flowr fills the gap: a declarative, validatable, toolable format for workflows that branch on evidence rather than control flow.

→ **[Full specification with examples and visual diagrams](https://nullhack.github.io/flowr/)**

---

## The reference implementation

This repository contains a Python reference implementation — a CLI and library that validates, queries, and tracks flow definitions conforming to the specification. The specification is the contract; this code is one tool that honours it.

```
flowr validate deploy.yaml          →  valid: True
flowr states deploy.yaml            →  prepare, execute, review
flowr next deploy.yaml review       →  approve → deployed [blocked]  need: score=>=80
                                      →  reject → failed
flowr transition deploy.yaml review approve --evidence score=85
                                      →  from: review, to: deployed
flowr session init deploy-flow       →  session created at state: prepare
flowr --session transition approve  →  from: prepare, to: review
flowr mermaid deploy.yaml           →  stateDiagram-v2 ...
```

**Validation.** Structural constraints — missing fields, ambiguous targets, cross-flow cycles, subflow exit contracts — checked against the specification.

**Query.** States, transitions, conditions, attributes — ask any question the flow can answer.

**Sessions.** Init, show, set-state, transition, list. Subflow push/pop for nested workflows. Auto-enters initial subflow on `session init`. One `--session` flag turns any command session-aware.

**Config.** `flowr config` shows where every value comes from — default, pyproject.toml, or CLI override.

**Mermaid export.** Generate state diagrams from any flow definition.

---

## Quick start

Install:

```bash
pip install flowr
```

Requires Python 3.13+.

Define a flow:

```yaml
flow: deploy
version: 1.0.0
exits: [deployed, failed]

states:
  - id: prepare
    next:
      ready: execute

  - id: execute
    next:
      success: deployed
      error: failed

  - id: review
    next:
      approve:
        to: deployed
        when: { score: ">=80" }
      reject: failed
```

Use it:

```bash
$ flowr validate deploy.yaml
valid: True

$ flowr states deploy.yaml
prepare
execute
review

$ flowr next deploy.yaml review
state: review
  approve → deployed [blocked]  need: score=>=80
  reject → failed

$ flowr transition deploy.yaml review approve --evidence score=85
from: review
trigger: approve
to: deployed

$ flowr session init deploy-flow
flow: deploy-flow
state: prepare
name: default

$ flowr --session transition approve
from: prepare
trigger: approve
to: review

$ flowr session show
flow: deploy-flow
state: review
name: default
stack: (none)

$ flowr config
project_root = /my/project  (default)
flows_dir = .flowr/flows  (default)
sessions_dir = .flowr/sessions  (default)
default_flow = main-flow  (default)
default_session = default  (default)
```

---

## Who is this for?

### Specification adopters

You build editors, visualizers, CI systems, or orchestration layers. You need a structural format for workflow state machines — not an execution engine. The flowr specification gives you states, transitions, guard conditions, and subflows in a declarative YAML format with a conforming validator. Any tool can parse it. [Read the spec.](https://nullhack.github.io/flowr/)

### Agent operators

You run `flowr check`, then `flowr transition`, then `flowr check` again — each time passing the flow name and current state by hand. Or you let sessions track it: `flowr session init deploy-flow`, `flowr --session transition approve`, `flowr --session check`. The session file remembers where you are. Push into a subflow; pop back out. No state to reconstruct, no context to pass.

### Developers

You write a flow YAML. You need to know: is it valid? Which states can I reach from here? Does this transition have guard conditions? `flowr validate`, `flowr states`, `flowr next`, `flowr check` answer these questions — from the terminal for humans, from the Python library for tools.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `flowr validate <flow>` | Validate a flow definition |
| `flowr states <flow>` | List all state ids |
| `flowr check <flow> <state> [<target>]` | Show state details or transition conditions |
| `flowr next <flow> <state> [--evidence K=V]` | Show all transitions with trigger→target and condition status |
| `flowr transition <flow> <state> <trigger> [--evidence K=V]` | Compute next state |
| `flowr mermaid <flow>` | Export as Mermaid state diagram |
| `flowr session init <flow> [--name NAME]` | Create a new session (auto-enters initial subflow) |
| `flowr session show [--name NAME] [--format FORMAT]` | Display current session state |
| `flowr session set-state <state> [--name NAME]` | Update the session's current state |
| `flowr session list [--format FORMAT]` | List all sessions |
| `flowr config [--json]` | Show resolved configuration with sources |
| `flowr --session <command>` | Run a command using session state (works with validate, states, check, next, transition) |

`<flow>` accepts a file path or a short flow name (resolved from `.flowr/flows/`). Use `--flows-dir` to override the configured flows directory. All commands accept `--json` for machine-readable output. Evidence: `--evidence key=value` (repeatable) or `--evidence-json '{"key": "value"}'`.

---

## Architecture

```
flowr/
├── domain/           # Core domain — Flow, State, Transition, Session, conditions, validation
│   ├── flow_definition.py
│   ├── loader.py
│   ├── session.py
│   ├── condition.py
│   ├── validation.py
│   └── mermaid.py
├── infrastructure/   # Adapters — config resolution, session persistence
│   ├── config.py
│   └── session_store.py
├── cli/              # Primary adapter — CLI commands, resolution, output formatting
│   ├── resolution.py
│   ├── session_cmd.py
│   └── output.py
└── __main__.py       # CLI entrypoint — argparse dispatch
```

Hexagonal architecture. Domain has no infrastructure dependencies. CLI is the primary adapter. Session store is a secondary adapter behind a Protocol port.

---

## Documentation

- **[Specification](https://nullhack.github.io/flowr/)** — the flowr format with examples and visual diagrams
- **[Flow Definition Specification](https://github.com/nullhack/flowr/blob/main/docs/spec/flow_definition_spec.md)** — authoritative YAML format reference
- **[System Overview](https://github.com/nullhack/flowr/blob/main/docs/spec/system.md)** — architecture, domain model, module structure
- **[Product Definition](https://github.com/nullhack/flowr/blob/main/docs/spec/product_definition.md)** — product boundaries, users, and scope

---

## Development

```bash
uv sync --all-extras       # install with dev dependencies
uv run task test            # run tests
uv run task test-fast       # fast tests only
uv run task test-build      # full suite with coverage
uv run task lint            # lint and format
uv run task static-check    # type checking
```

---

## License

MIT — see [LICENSE](LICENSE).
