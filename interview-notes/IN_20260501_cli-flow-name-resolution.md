# IN_20260501_cli-flow-name-resolution — CLI flow name resolution

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## Feature: cli-flow-name-resolution

| ID | Question | Answer |
|----|----------|--------|
| Q1 | What is the core problem with the current CLI flow argument? | The CLI `flow_file` argument only accepts literal file paths like `.flowr/flows/feature-development-flow.yaml`. Short flow names like `feature-development-flow` fail with "File not found" even though the YAML exists in the configured flows directory. |
| Q2 | Where does this mismatch cause friction? | Session YAML files store the flow name (not the full path). Documentation references flow names. Agents copy flow names from session YAML and pass them to CLI commands, which then fail. The session store and the CLI use different identifiers for the same flow. |
| Q3 | What is the proposed resolution mechanism? | Name resolution at the CLI layer: if the `flow_file` argument is not an existing file path, treat it as a flow name and resolve it by appending `.yaml` and looking in the configured `flows_dir`. Uses the existing `resolve_config()` infrastructure. |
| Q4 | Should library functions change? | No — library functions (`load_flow_from_file`, `resolve_subflows`) stay unchanged. They take `Path` arguments. Resolution is a CLI-layer concern only. |
| Q5 | What happens when a flow name doesn't match any file in `flows_dir`? | The CLI should report a clear, actionable error: the flow name was not found in the configured flows directory. No dead-end "File not found" that leaves the user guessing whether the name or the path was wrong. |
| Q6 | Should file paths still work? | Yes — absolute and relative file paths must continue to work exactly as before. If the argument resolves to an existing file, use it directly. Name resolution is a fallback, not a replacement. |
| Q7 | How does the `--flows-dir` flag interact with name resolution? | The `--flows-dir` global flag overrides the `pyproject.toml` `flows_dir` value for the current invocation. Name resolution uses whichever `flows_dir` is active (config or flag). |
| Q8 | Should the CLI try multiple extensions (`.yaml`, `.yml`)? | SA decision — deferred to system-architect for extension resolution strategy. |
| Q9 | Should name resolution be case-sensitive? | Yes — flow names are exact matches. Case-sensitive on all platforms. |
| Q10 | Pre-mortem: what happens if a flow name matches a file that also exists at a relative path? | File path takes priority. If the argument resolves to an existing file, use it. Name resolution only activates when the argument is not a valid file path. |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA1 | Usability | When a developer passes a short flow name to the CLI, the system resolves it to the correct file or reports a clear error identifying the flow name and the directory searched | Error message includes flow name and searched directory | Must |
| QA2 | Backward Compatibility | When a developer passes an existing file path (absolute or relative), the CLI behaves identically to the current version | Zero behavior change for existing file-path invocations | Must |

---

## Pain Points Identified

- CLI rejects short flow names that are valid identifiers in session YAML and documentation, forcing users to type or copy full paths
- Session store uses flow names but the CLI cannot accept them — the two subsystems use different identifiers for the same concept
- Agents that read flow names from session YAML and pass them to CLI commands get "File not found" errors with no guidance on how to fix the argument

## Business Goals Identified

- CLI and session store should use the same identifiers — a flow name that works in one context should work in the other
- Reduce friction for agents and humans by eliminating the need to construct file paths for flows that already have well-known names

## Terms to Define (for glossary)

- Flow Name Resolution — the CLI-layer process of converting a short flow name to a file path by looking in the configured flows directory
- flows_dir — the configurable directory containing flow definition YAML files (existing term, may need update to note CLI name resolution usage)

## Action Items

- [ ] SA to resolve deferred decision on extension resolution strategy (Q8)
- [ ] Write .feature file for cli-flow-name-resolution