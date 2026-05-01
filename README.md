<img src="docs/assets/banner.svg" alt="flowr — non-deterministic state machine specification to knead workflows" width="100%">

# flowr

> **⚠️ Beta — do not install.** This project is under active development with breaking changes in progress. The API, package structure, and configuration may change without notice until the first stable release.

Non-deterministic state machine specification to knead workflows.

`flowr` is a Python library and CLI for defining, validating, and visualising workflow state machines in YAML. Define your flows in a declarative format, validate them against the specification, query states and transitions, and export Mermaid diagrams — all from the terminal or programmatically.

## Install

```bash
pip install flowr
```

Requires Python 3.13+.

## Quick Start

Create a flow definition YAML file:

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

Validate it:

```bash
$ flowr validate deploy.yaml
valid: True
```

Query states and transitions:

```bash
$ flowr states deploy.yaml
prepare
execute
review

$ flowr next deploy.yaml review
state: review
next: approve (guarded)
next: reject

$ flowr transition deploy.yaml review approve --evidence score=85
from: review
trigger: approve
to: deployed
```

Export as Mermaid:

```bash
$ flowr mermaid deploy.yaml
stateDiagram-v2
    state "prepare" as prepare
    state "execute" as execute
    state "review" as review
    ...
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `flowr validate <file>` | Validate a flow definition |
| `flowr states <file>` | List all state ids |
| `flowr check <file> <state> [<target>]` | Show state details or transition conditions |
| `flowr next <file> <state> [--evidence K=V]` | Show valid next transitions |
| `flowr transition <file> <state> <trigger> [--evidence K=V]` | Compute next state |
| `flowr mermaid <file>` | Export as Mermaid state diagram |

All commands accept `--json` for machine-readable output.

Evidence can be passed with `--evidence key=value` (repeatable) or `--evidence-json '{"key": "value"}'`.

## Documentation

- **[flowr docs](https://nullhack.github.io/flowr/)** — hosted documentation
- **[Flow Definition Specification](docs/spec/flow_definition_spec.md)** — authoritative YAML format reference (fields, conditions, subflows, validation rules)
- **[System Overview](docs/spec/system.md)** — architecture, domain model, module structure, and API
- **[Product Definition](docs/spec/product_definition.md)** — product boundaries, users, and scope

## Development

```bash
# Install with dev dependencies
uv sync --all-extras

# Run tests
uv run task test

# Fast tests (skip slow)
uv run task test-fast

# Full test suite with coverage
uv run task test-build

# Lint and format
uv run task lint

# Type checking
uv run task static-check
```

## License

MIT