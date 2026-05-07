# IN_20260501_session-management — Session management for CLI

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## Feature: session-management

| ID | Question | Answer |
|----|----------|--------|
| Q1 | What is the core problem with the current CLI? | Every CLI invocation is stateless — each command is independent with no memory of previous invocations. Agents must manually track which flow and state they are in, read session YAML files themselves, and construct the correct `flow_file` + `state` arguments for each command. |
| Q2 | How does the session YAML relate to this? | The session YAML already exists in `.flowr/sessions/` and stores the current flow name and state. But the CLI doesn't use it — agents have to read and update it manually, which is error-prone and creates friction. |
| Q3 | What subcommands should session management provide? | Three: `session init <flow>` creates a new session at the flow's initial state; `session show` displays the current session's flow, state, and attrs; `session set-state <state>` updates the session's current state. |
| Q4 | How should existing commands become session-aware? | Add a `--session` flag to `next`, `transition`, and `check`. When present, these commands read the session file for the flow name and current state instead of requiring them as arguments. After a `transition`, the session file is auto-updated with the new state. |
| Q5 | Should `--session` require a session name or use a default? | `--session` takes an optional session name. If omitted, it uses the default session (the most recently created or explicitly selected session). SA decides the exact default resolution strategy. |
| Q6 | What output formats should session commands support? | `--format yaml|json` on `session show` and `session set-state`. Default is YAML for human readability, JSON for programmatic use. |
| Q7 | How should session state be persisted? | Write to the session YAML file in `.flowr/sessions/`. Use atomic writes (write to temp file, then rename) to prevent partial state corruption. |
| Q8 | What happens with subflows — does session track subflow state? | Yes — use a push/pop stack. When a transition enters a subflow state, push the parent flow+state onto the stack and track the subflow's current state. When the subflow exits, pop the stack and resume the parent at the exit target state. |
| Q9 | Should non-session CLI commands change? | No — commands without `--session` work exactly as before. Session awareness is opt-in via the flag. Backward compatibility is absolute. |
| Q10 | What if a session file is corrupted or manually edited incorrectly? | SA decision — deferred to system-architect for validation and error recovery strategy. |
| Q11 | Should `session init` accept params for the flow? | SA decision — deferred to system-architect for param passing mechanism. |
| Q12 | Should there be a `session list` command? | Yes — `session list` shows all sessions in the sessions directory with their flow, state, and last-updated timestamp. |
| Q13 | Pre-mortem: what happens if two processes write the same session file simultaneously? | SA decision — deferred to system-architect for concurrency strategy. Likely: last-write-wins with atomic writes is acceptable for single-user CLI usage. |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA1 | Reliability | When a session file is written, the write is atomic — no partial or corrupted state is possible even on crash or interrupt | Atomic write via temp-file-then-rename | Must |
| QA2 | Usability | When an agent or human runs a session-aware command, the CLI automatically reads and updates session state without manual file manipulation | Single `--session` flag enables session mode | Must |
| QA3 | Backward Compatibility | When a developer runs a CLI command without `--session`, the command behaves identically to the current version | Zero behavior change for non-session invocations | Must |
| QA4 | Usability | When a developer runs `session show`, the output clearly presents the current flow, state, and attrs in the requested format | YAML default with optional JSON via `--format` | Should |

---

## Pain Points Identified

- Every CLI invocation is stateless — agents must manually track which flow and state they are in across invocations
- The session YAML already stores workflow state but the CLI doesn't read or write it, forcing agents to do manual file I/O
- Copying flow names and state names from session YAML to CLI arguments is error-prone and creates friction in the workflow
- No push/pop mechanism for subflows means agents must manually track parent flow context when entering and exiting subflows

## Business Goals Identified

- Persistent workflow state across CLI invocations so agents and humans can resume where they left off without manual state tracking
- Eliminate the mismatch between session store identifiers and CLI arguments by making the CLI session-aware
- Enable subflow navigation with automatic push/pop so agents can enter and exit subflows without losing parent context

## Terms to Define (for glossary)

- Session — a persistent record of workflow state (flow name, current state, attrs) that survives across CLI invocations
- Session Store — the directory (`.flowr/sessions/`) containing session YAML files
- Session-Aware — a CLI command that reads and/or updates session state via the `--session` flag
- Subflow Push/Pop — the mechanism for tracking parent flow context when entering a subflow (push) and restoring it on exit (pop)

## Action Items

- [ ] SA to resolve deferred decisions (Q10, Q11, Q13)
- [ ] Write .feature file for session-management