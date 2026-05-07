# IN_20260426_cli_design — CLI design session

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## Feature: flowr-cli

| ID | Question | Answer |
|----|----------|--------|
| Q34 | Should the CLI be purely one-shot or support an interactive mode? | One-shot only — each command is a separate invocation, no interactive/REPL mode. |
| Q35 | What should the check command show? | Multiple commands: check shows state details, next shows possible next states. check <flow> <state> <target> shows conditions for a specific transition. |
| Q36 | What should next show given state + evidence? | Show passing transitions only — evaluate guard conditions and show only transitions whose conditions pass. |
| Q37 | Should goto be stateless or session-based? | Stateless transition — compute the next state given current state + trigger + evidence, print result. No session file. |
| Q38 | For image, should the CLI call an external tool or just output Mermaid text? | SA decision — deferred to system-architect for implementation approach. |
| Q39 | Should validate be a subcommand? | Yes — a separate validate subcommand that checks a flow definition against the spec. |
| Q40 | What output format should CLI commands produce? | Text by default, JSON with a --json flag for programmatic use. |
| Q41 | How should evidence be provided to next and transition? | SA decision — deferred to system-architect for interface design. |
| Q42 | When transition leads to a subflow state, what happens? | Enter the subflow's first state — moving to a "flow state" starts the subflow at its initial state. |
| Q43 | Should the CLI support loading multiple flow definitions at once? | Yes — subflows are loaded automatically by reference from the root flow. |
| Q44 | Confirm the full list of CLI subcommands. | Confirmed list: validate, states, check, next, transition, mermaid, image. |
| Q45 | Alternative names for goto? | transition — chosen by stakeholder as the command name. |
| Q46 | How should the CLI find subflow files? | SA decision — deferred to system-architect for lookup strategy. |
| Q47 | Should next show what evidence each transition requires? | Yes — check <flow> <state> <target> shows required conditions. |
| Q48 | Should there be a states command? | Yes — a separate states command that lists all states in a flow. |
| Q49 | What should validate output? | SA decision — deferred to system-architect for output format. |
| Q50 | Should condition checking be part of check or a separate command? | Same command, different args — check <flow> <state> shows state details, check <flow> <state> <target> shows conditions. |
| Q51 | When transition enters a subflow, should output show subflow name + first state or just first state? | SA decision — deferred to system-architect. |
| Q52 | Should CLI commands use exit codes for pass/fail? | SA decision — deferred to system-architect. |
| Q53 | Is the primary input for all commands a single YAML file path? | SA decision — deferred to system-architect for input interface design. |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA5 | Usability | When a developer runs a CLI subcommand, the output is unambiguous and actionable | Key-value text format with clear error messages | Must |

---

## Pain Points Identified

- Many design decisions deferred to SA for implementation approach

## Business Goals Identified

- A consistent, Unix-y CLI that is easy to script and pipe

## Terms to Define (for glossary)

- CLI Subcommand
- Flow Loading

## Action Items

- [ ] SA to resolve deferred decisions (Q38, Q41, Q46, Q49, Q51, Q52, Q53)
- [ ] Write .feature file for flowr-cli