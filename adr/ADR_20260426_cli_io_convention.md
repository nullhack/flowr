# ADR_20260426_cli_io_convention

## Status

Accepted

## Context

The flowr CLI needs 7 subcommands that all operate on flow definition YAML files. Three subcommands (next, transition, check conditions) require evidence input. All subcommands need consistent output formatting for both human and machine consumption.

## Interview

| Question | Answer |
|---|---|
| Primary input? | Single YAML file path as positional arg (e.g. `flowr validate myflow.yaml`) |
| Evidence input? | `--evidence key=value` repeated flags for simple cases; `--evidence-json` flag for complex/nested JSON evidence |
| Exit codes? | 0 = success, 1 = command failed (validation errors, no passing transitions, etc.), 2 = usage error (bad args, missing file) |
| Validate output? | Always list all violations (not exit-code-only) |
| Output channels? | stdout for results, stderr for errors/warnings |
| Text output format? | Key-value pairs, one per line |

## Decision

Single YAML path as positional arg; `--evidence key=value` flags for simple cases + `--evidence-json` for JSON evidence; 3-tier exit codes (0/1/2); list all violations; stdout for results / stderr for errors; key-value text output.

## Reason

Simplest consistent UX across all subcommands; follows Unix conventions; enables piping and scripting.

## Alternatives Considered

- **Directory auto-discovery**: adds ambiguity about root flow; YAGNI
- **YAML evidence file**: overkill for v1; can be added later
- **JSON evidence string only**: poor UX with shell escaping for simple cases
- **Exit code only**: useless for debugging
- **Everything on stdout**: breaks piping
- **Table/YAML text output**: over-engineered; --json exists for structured needs

## Consequences

- (+) Consistent, Unix-y CLI; easy to script and pipe
- (+) --json flag covers all machine-readable use cases
- (+) --evidence-json supports complex/nested evidence values
- (-) Flat evidence via --evidence is limited to key=value pairs (mitigated: --evidence-json for complex cases)

## Risk Assessment

| Risk | Probability | Impact | Mitigation | Accepted? |
|------|------------|--------|------------|-----------|
| Flat key=value evidence limits complex inputs | Low | Low | --evidence-json flag mitigates for complex cases | Yes |