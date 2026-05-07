# IN_20260502_config-paths-gap — Config introspection subcommand gap analysis

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## Feature: configurable-paths (gap — Config introspection rule)

The configurable-paths feature has 6 @id examples. Three (971ec591, 5e0dd562, 076da303) are already implemented by the cli-flow-name-resolution feature. The remaining three (2e301322, 36d41122, 9d4c4973) require a `flowr config` subcommand that does not yet exist.

| ID | Question | Answer |
|----|----------|--------|
| Q74 | What should `flowr config` display? | Each resolved configuration key, its value, and the source of that value (default, pyproject.toml, or cli). |
| Q75 | Should `flowr config` show all config keys or only flows_dir? | All resolved keys in v1: flows_dir, sessions_dir, default_flow, default_session. |
| Q76 | What output format should `flowr config` use? | Human-readable table by default. The existing `--json` flag should produce JSON output (consistent with other commands). |
| Q77 | Should `flowr config` also show the project root? | Yes — show `project_root` with its resolved path and source (cwd or cli). This helps users debug path resolution. |
| Q78 | What happens when `--flows-dir` is passed to `flowr config`? | The overridden value is shown with source "cli" instead of "pyproject.toml" or "default". This is already covered by @id:9d4c4973. |
| Q79 | Should `flowr config` validate that configured directories exist? | No — it shows the resolved configuration, not whether the paths are valid. Path validation is a separate concern (handled by the commands that use those paths). |
| Q80 | What if pyproject.toml doesn't exist? | `flowr config` shows all keys with source "default" and their default values. This is covered by @id:36d41122. |
| Q81 | Pre-mortem: what if a key in [tool.flowr] has an invalid type? | ConfigError is raised with a clear message. The config command itself doesn't validate types beyond what `resolve_config()` already does. |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA9 | Consistency | When a user runs `flowr config`, the output format is consistent with `flowr check --json` | Same JSON structure pattern | Must |
| QA10 | Completeness | When all config keys are shown, no key is missing that affects CLI behavior | All 5 keys shown | Must |

---

## Pain Points Identified

- No way to verify which configuration values are in effect without running a command and observing behavior
- When `--flows-dir` overrides the config, there's no way to confirm the override took effect

## Business Goals Identified

- Provide visibility into resolved configuration for debugging and verification
- Complete the configurable-paths feature by implementing the only remaining rule (Config introspection)

## Terms to Define

- Config introspection — already defined in glossary as part of configurable-paths
- Config source — the origin of a configuration value: "default", "pyproject.toml", or "cli"

## Action Items

- [ ] Update configurable-paths.feature to mark covered examples
- [ ] Create BDD scenarios for the 3 remaining @id examples
- [ ] Create test stubs and implement `flowr config` subcommand