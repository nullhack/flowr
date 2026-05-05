<div align="center">

<img src="docs/assets/banner.svg" alt="flowr — non-deterministic state machine specification to knead workflows" width="100%"/>

<br/><br/>

[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen?style=for-the-badge)](https://nullhack.github.io/flowr/coverage/)
[![CI](https://img.shields.io/github/actions/workflow/status/nullhack/flowr/ci.yml?style=for-the-badge&label=CI)](https://github.com/nullhack/flowr/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-%E2%89%A513.0-blue?style=for-the-badge)](https://www.python.org/downloads/)
[![PyPI](https://img.shields.io/pypi/v/flowr?color=%2300FF41&style=for-the-badge)](https://pypi.org/project/flowr/)
[![MIT License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](https://github.com/nullhack/flowr/blob/main/LICENSE)

**Define workflow state machines in YAML. Validate, query, and track them from the terminal.**

</div>

---

> **⚠️ Beta — do not install.** This project is under active development. The API, package structure, and configuration may change without notice until the first stable release.

You write a flow definition in YAML. flowr checks that it is structurally valid, tells you what states exist and which transitions are available, and keeps track of where you are — across invocations, across subflows. One specification format. One CLI. No runtime engine, no side effects, no opinions about what your workflow should *do* — only what it *is* and whether it *holds together*.

---

## Who is this for?

### Agent Operators — Persist workflow state across CLI invocations

You run `flowr check`, then `flowr transition`, then `flowr check` again — each time passing the flow name and current state by hand. Or you let sessions track it: `flowr session init deploy-flow`, `flowr --session transition approve`, `flowr --session check`. The session file remembers where you are. Push into a subflow; pop back out. No state to reconstruct, no context to pass.

### Developers — Validate and query workflow definitions from code or terminal

You write a flow YAML. You need to know: is it valid? Which states can I reach from here? Does this transition have guard conditions? `flowr validate`, `flowr states`, `flowr next`, `flowr check` answer these questions — from the terminal for humans, from the Python library for tools.

### Tool Authors — Build on a specification, not a runtime

flowr defines a YAML format for non-deterministic state machines with per-state attributes, guard conditions, and subflows. The validator enforces structural constraints. The library parses flows into dataclasses. No execution engine, no side-effect hooks — a clean foundation for editors, visualizers, or orchestration layers.

---

## What it does

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

**Sessions.** Init, show, set-state, transition, list. Subflow push/pop for nested workflows. Auto-enters initial subflow on `session init`. One `--session` flag turns any command session-aware (including `validate` and `states`).

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

## Why does this exist

No existing YAML standard covers non-deterministic state machine workflows with per-state agent assignment and filesystem-as-source-of-truth. Existing solutions (XState, SCXML, Serverless Workflow, BPMN) target execution engines or deterministic workflows. flowr fills this gap: a declarative, validatable, toolable format for workflows that branch on evidence rather than control flow.

---

## Documentation

- **[flowr docs](https://nullhack.github.io/flowr/)** — hosted documentation
- **[Flow Definition Specification](docs/spec/flow_definition_spec.md)** — authoritative YAML format reference
- **[System Overview](docs/spec/system.md)** — architecture, domain model, module structure
- **[Product Definition](docs/spec/product_definition.md)** — product boundaries, users, and scope

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