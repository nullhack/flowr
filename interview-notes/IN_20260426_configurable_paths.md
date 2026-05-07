# IN_20260426_configurable_paths — Configurable paths session

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Scope refinement

---

## Feature: configurable-paths

| ID | Question | Answer |
|----|----------|--------|
| Q66 | What exactly should be configurable? Just flows dir and session dir, or more? | Just the flows dir for now. Keep it simple. |
| Q67 | Should flowr validate <file> still accept a direct file path, or should it also support name-based lookup from the configured directory? | Direct file path only — no name-based lookup. The existing CLI interface stays unchanged. |
| Q68 | Should library functions (load_flow_from_file, resolve_subflows) use configured paths or stay explicit? | Library functions stay explicit — they take Path arguments. Configuration only affects the CLI layer. |
| Q69 | What should the exact defaults be for flows_dir? | SA decides — deferred. |
| Q70 | Should there be a flowr config CLI command? | Yes — flowr config prints current resolved configuration, showing each key, its value, and where it came from. |
| Q71 | Should configuration be overridable at the command line? | Yes — --flows-dir CLI flag overrides the pyproject.toml value for a single invocation. |
| Q72 | Should the session directory be configurable too? | SA decides — session directory is deferred. |
| Q73 | Pre-mortem: what happens with misconfigured paths? | SA decides — misconfigured path handling is deferred. |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA8 | Simplicity | When a developer configures flows_dir, it requires only one line in pyproject.toml | Single-line configuration | Must |

---

## Pain Points Identified

- Hardcoded paths limit flexibility for non-standard project layouts

## Business Goals Identified

- Allow project-specific configuration of flow directory location without changing library API

## Terms to Define (for glossary)

- Flows Directory
- Configuration

## Action Items

- [ ] SA to resolve deferred decisions (Q69, Q72, Q73)
- [ ] Write .feature file for configurable-paths