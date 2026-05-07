# IN_20260507_export-robustness: Post-PR robustness fixes for export and CLI error handling

## Pain Points

1. **Cross-adapter flag confusion** — `flowr export --format mermaid --flat` silently ignores `--flat`. Users may believe the flag had an effect. All adapter flags visible in help regardless of selected format.
2. **Empty directory silent success** — `flowr export --format json /tmp/empty` returns `[]` with exit code 0. No indication that no flows were found. Masks user mistakes (wrong directory).
3. **YAML parse traceback leak** — Malformed YAML crashes the CLI with a full Python traceback across all commands (validate, export, states, check, next, transition). Pre-existing defect predating the export feature.

## Business Goals

1. Improve CLI reliability — users should never see raw Python tracebacks
2. Clear feedback — every CLI invocation should produce unambiguous output about what happened
3. Consistent error handling — all commands handle malformed input gracefully

## Terms to Define

No new domain terms needed — these are edge-case fixes within existing concepts (Export Adapter, Export Registry, Format Resolution).

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA1 | Usability | When a user passes a flag irrelevant to the selected export format, the CLI warns them | Warning on stderr listing unused flag(s) | Should |
| QA2 | Correctness | When a user exports from an empty directory, the CLI reports failure | Error message on stderr, exit code 1 | Must |
| QA3 | Reliability | When a user passes a malformed YAML file to any CLI command, the CLI produces a user-friendly error | Single-line error on stderr, no traceback, exit code 1 | Must |

## Scope Confirmation

- **Cross-adapter flags:** Warn on unused flags (stderr warning listing irrelevant flag names)
- **Empty directory:** Error message + exit code 1
- **YAML traceback:** Fix across all commands (add `yaml.YAMLError` catch in `main()`)
- **Not in scope:** Changing flag registration, two-pass argparse, new domain types

## Resolved Decisions

- Format: warn on unused adapter flags (stakeholder chose over document-and-accept)
- Empty dir: exit code 1 (error, not warning)
- YAML: fix all commands, not just export
