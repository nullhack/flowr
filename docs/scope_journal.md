# Scope Journal: flowr

---

## 2026-04-22 — Session 1

Status: COMPLETE

### General

| ID | Question | Answer |
|----|----------|--------|
| Q1 | Who are the users? | Python engineers starting a new project who want rigorous tooling without the setup cost. |
| Q2 | What does the product do at a high level? | Provides a fully configured Python project skeleton: CI, quality tooling, test infrastructure, and an AI-assisted five-step delivery workflow. |
| Q3 | Why does it exist — what problem does it solve? | Setting up a production-grade Python environment from scratch is expensive and often skipped; engineers then accrue quality debt from day one. |
| Q4 | When and where is it used? | At project inception — cloned once, then evolved as features are added via the built-in workflow. |
| Q5 | Success — what does "done" look like? | An engineer clones the template and ships a meaningful first feature within a single session, with all quality gates passing. |
| Q6 | Failure — what must never happen? | The template introduces more friction than it removes, or locks engineers into choices they cannot override. |
| Q7 | Out-of-scope — what are we explicitly not building? | Runtime infrastructure (databases, queues, cloud deployment), UI frameworks, domain-specific business logic. |

### Runtime Behaviour

| ID | Question | Answer |
|----|----------|--------|
| Q8 | Should the template ship with any working feature, or be purely empty? | It should ship with exactly one working demonstration feature so engineers see the full workflow end-to-end. |

### Feature: cli-entrypoint

| ID | Question | Answer |
|----|----------|--------|
| Q9 | Which behavioural areas are in scope for the template's own feature backlog? | Just one simple command in the base package — useful for any starting project, simple enough not to bloat the app, and showcasing the template's capabilities end-to-end. |
| Q10 | What kind of command would be "useful for any starting project"? Candidate options presented: version, hello/greet, info/about, config show, health. | Stakeholder asked: "if I choose version, what will it add to my app/ folder?" — confirmed interest in version-style command after seeing the footprint (one file, ~10 lines, zero new dependencies). |
| Q11 | Three options presented: (A) `--help` only, (B) `--version` only, (C) `--help` + `--version` combined. Stakeholder also asked how a help/usage command would look in code and terminal. Full code sketches and tradeoff table provided. Which option for the demonstration feature? | Option C — `--help` + `--version` combined. `python -m flowr --help` shows app name, tagline, and available options. `python -m flowr --version` shows `flowr <version>` read from package metadata. Zero new dependencies, all code in `flowr/__main__.py`. |

---

## 2026-04-26 — Session 2

Status: COMPLETE

### General

| ID | Question | Answer |
|----|----------|--------|
| Q12 | Who are the users of the flow definition specification? (Re-asked: project scope has shifted from "Python project template" to "flow specification format") | Two user groups: developers/engineers who write and validate flow definitions, and tool authors who build tooling (validators, converters, editors) that consume the specification format. |
| Q13 | What does the product do at a high level? (Re-asked: the product is now a specification, not a template) | Three capabilities: define (YAML format for non-deterministic state machine workflows), validate (reference validator that checks conformance), and visualize (Mermaid converter that produces diagrams from flow definitions). |
| Q14 | Why does it exist — what problem does it solve? | No existing standard covers defining non-deterministic state machine workflows in YAML. Existing standards (XState, SCXML, etc.) don't address flowr's core features: per-state agent assignment, AI-agent-as-runtime, and filesystem-as-source-of-truth. |
| Q15 | When and where is it used? (Who reads flow definitions? Who writes them? Who validates them?) | Both humans and machines write and validate flows. Humans author flow YAML files; machines (validators, converters) parse and check them. |
| Q16 | Success — what does "done" look like for v1? (Issue #3 defines the spec format, but what's the deliverable?) | Three deliverables: prose specification document, reference validator (Python module), and Mermaid converter. No JSON Schema (see Q27 — internal representation uses Python dataclasses; JSON is for CLI communication only). |
| Q17 | Failure — what must never happen? (What would make the specification format worse than having no specification?) | Ambiguity — the specification must not leave room for contradictory implementations. If two conforming implementations can interpret the same flow definition differently, the spec has failed. |
| Q18 | Out-of-scope for v1 — what are we explicitly not building? (Issue #3 lists some items, but where's the line between "specification" and "implementation"?) | No runtime engine and no session tracking in v1. The v1 scope is limited to the flow definition format itself. Session tracking is deferred to a future version. |

### Specification Semantics

| ID | Question | Answer |
|----|----------|--------|
| Q19 | The spec says state-level `attrs` "override/extend" flow-level `attrs`. What are the merge semantics — deep merge (nested dicts merged recursively), shallow replace (state-level dict replaces flow-level dict entirely), or something else? | Replace entirely. State-level attrs completely replace flow-level attrs — no merge, no deep merge, no extension. If a state defines attrs, those attrs are the full dict for that state. |
| Q20 | The `~=value` condition operator is defined as "approximate match" — for strings: "case-insensitive substring." Does `~=pass` match `passing_grade`? What's the exact matching rule — is it "evidence contains condition as a case-insensitive substring" or "evidence equals condition ignoring case"? | ~~Original answer: Fuzzy string match: substring, case insensitive, small typos tolerated.~~ **Revised at architecture (Step 2):** The `~=` operator applies ONLY to numeric values with 5% tolerance. String fuzzy matching was removed as too complicated and prone to interpretation. See ADR-2026-04-26-fuzzy-match-algorithm. |
| Q21 | The spec says `>=80%` "compares 80" — does it strip `%` from both the condition value AND the evidence value? If evidence is `75%`, is it compared as 75 vs 80? What about `>=80` with evidence `75%` — does the `%` get stripped from evidence too? | Numeric extraction strips from both condition AND evidence. `>=80%` vs evidence `75%` compares 80 vs 75. `>=80` vs evidence `75%` also strips the `%` from evidence, comparing 80 vs 75. |
| Q22 | What happens when a `next` target matches both a state id AND an exit name? The spec says "found in states → internal transition; found in exits → subflow exit" but doesn't specify priority when both match. | Validation error. A next target that matches both a state id and an exit name is ambiguous and must be rejected at load time. State ids and exit names cannot share the same name within a flow. |
| Q23 | The spec forbids "cross-flow cycles" but the project's own flows have within-flow cycles (e.g., `idle → step-1-scope → blocked → idle`). Are within-flow cycles allowed? Is the cycle detection rule only about parent→child→parent cycles? | Within-flow cycles are allowed. Only cross-flow cycles (parent→child→parent) are forbidden. The project's own flows use within-flow cycles extensively (e.g., idle→step-1-scope→blocked→idle). |
| Q24 | The spec says `params` is a "list of parameter names this flow expects (plain strings)." Can params have default values? What happens if a required param is missing when the flow is invoked? Is this a load-time validation error or a runtime error? | Params are declarations with optional default values. A param without a default value is required; if a required param is missing when the flow is invoked, it is a validation error. Params with default values are optional. |
| Q25 | Evidence values in conditions — are they typed? Is `==true` comparing against boolean `True` or the string `"true"`? How does the spec define the type system for evidence? In YAML, `true` is a boolean, but `==true` in a condition string is a string — how are they reconciled? | ~~Deferred to architect.~~ **Resolved at architecture (Step 2):** All evidence values are coerced to strings before comparison. YAML booleans become lowercase (`True` → `"true"`), YAML numbers become numeric strings (`80` → `"80"`). See ADR-2026-04-26-evidence-type-system. |

### Validation & Conformance

| ID | Question | Answer |
|----|----------|--------|
| Q26 | The spec defines validation rules but says "the library validates." Since v1 is "just the specification format," should v1 define conformance levels (e.g., "a conforming implementation MUST validate X, SHOULD validate Y")? | Yes. The specification defines two conformance levels: MUST (required for all conforming implementations) and SHOULD (recommended but not mandatory). |
| Q27 | Should the v1 deliverable include a JSON Schema for flow definitions, or is the prose specification sufficient? (Issue #2 recommends building one.) | No JSON Schema. The internal representation uses Python dataclasses; JSON is only for CLI communication. The prose specification plus the Python reference validator are sufficient. |
| Q28 | Should the v1 deliverable include a reference validator implementation (e.g., a Python module that validates flow definitions against the spec), or is that a separate deliverable? | Yes — include a reference validator as a Python module. It is part of the v1 deliverable, not a separate product. |
| Q29 | The session format includes `transitions` with "only counts >= 2 persisted." Why the threshold of 2? Is this configurable? What's the purpose of tracking transition counts at all? | Remove transition counts from the v1 spec. They add complexity without clear value for the flow definition format. |

### Feature: flow-definition-spec

| ID | Question | Answer |
|----|----------|--------|
| Q30 | What is the minimal v1 deliverable? Just the spec document? Spec + JSON Schema? Spec + validator? Spec + Mermaid converter? All of the above? | All deliverables: prose specification, Python reference validator, and Mermaid converter. (JSON Schema removed per Q27.) The existing flow YAML files (feature-flow.yaml, scope-cycle.yaml, arch-cycle.yaml, tdd-cycle.yaml) serve as reference examples that v1 must validate. |
| Q31 | Should the existing flow YAML files (feature-flow.yaml, scope-cycle.yaml, arch-cycle.yaml, tdd-cycle.yaml) serve as reference examples that v1 must validate? | Yes. The existing flow YAML files are reference examples that the v1 specification and validator must handle correctly. |
| Q32 | The spec mentions "Immutable loaded flows — edits produce copies" and "Session truth assumption — filesystem wins over session." Are these behavioral requirements for implementations, or design principles? Should v1 specify session behavior, or is that out of scope? | Immutable loaded flows is a MUST requirement. Filesystem truth is a SHOULD guideline. Session behavior is out of scope for v1 — the minimal session format includes only flow id and current state, no transitions. |
| Q33 | The spec in Issue #3 uses "flowception" terminology (e.g., "flowception's core features"). Should the v1 specification use "flowr" branding, or is "flowception" still the name of the specification format? | Format-agnostic naming. The specification format has its own name (independent of any implementation), and flowr is one implementation of that specification. The spec should not be branded as "flowr" or "flowception" — it defines a format that any tool can implement. |

---

## 2026-04-26 — Session 3

Status: IN-PROGRESS

### Feature: flowr-cli

| ID | Question | Answer |
|----|----------|--------|
| Q34 | Should the CLI be purely one-shot or support an interactive mode? | One-shot only — each command is a separate invocation, no interactive/REPL mode. |
| Q35 | What should the `check` command show? | Multiple commands: `check` shows state details, `next` shows possible next states. The user wants commands for all: check state details, check next states available given evidence requirements, check what conditions each transition requires. |
| Q36 | What should `next` show given state + evidence? | Show passing transitions only — given flow, state, and evidence, evaluate guard conditions and show only the transitions whose conditions pass. |
| Q37 | Should `goto` be stateless or session-based? | Stateless transition — compute the next state given current state + trigger + evidence, print result. No session file. |
| Q38 | For `image`, should the CLI call an external tool (mmdc) or just output Mermaid text? | SA decision — deferred to system-architect for implementation approach. |
| Q39 | Should `validate` be a subcommand? | Yes — a separate `validate` subcommand that checks a flow definition against the spec. |
| Q40 | What output format should CLI commands produce? | Text by default, JSON with a `--json` flag for programmatic use. |
| Q41 | How should evidence be provided to `next` and `transition`? | SA decision — deferred to system-architect for interface design. |
| Q42 | When `transition` leads to a subflow state, what happens? | Enter the subflow's first state — moving to a "flow state" starts the subflow at its initial state. Internal states of other-level flows are not available for nexts. |
| Q43 | Should the CLI support loading multiple flow definitions at once? | Yes — subflows are loaded automatically by reference from the root flow. The CLI resolves subflow references without the user having to specify each file. |
| Q44 | Confirm the full list of CLI subcommands. | Confirmed list: validate, states, check, next, transition, mermaid, image. Stakeholder asked for alternative names for `goto` → chose `transition`. |
| Q45 | Alternative names for `goto`? | `transition` — chosen by stakeholder as the command name. |
| Q46 | How should the CLI find subflow files? | SA decision — deferred to system-architect for lookup strategy. |
| Q47 | Should `next` show what evidence each transition requires? | Yes — there should be a command to check, given a valid next, it returns the required conditions. Confirmed as `check <flow> <state> <target>` (same command, different args). |
| Q48 | Should there be a `states` command? | Yes — add a separate `states` command that lists all states in a flow. |
| Q49 | What should `validate` output? | SA decision — deferred to system-architect for output format. |
| Q50 | Should condition checking be part of `check` or a separate command? | Same command, different args — `check <flow> <state>` shows state details, `check <flow> <state> <target>` shows conditions for a specific transition. |
| Q51 | When `transition` enters a subflow, should output show subflow name + first state or just first state? | SA decision — deferred to system-architect. |
| Q52 | Should CLI commands use exit codes for pass/fail? | SA decision — deferred to system-architect. |
| Q53 | Is the primary input for all commands a single YAML file path? | SA decision — deferred to system-architect for input interface design. |

Status: COMPLETE

---

## 2026-04-26 — Session 5

Status: COMPLETE

### Feature: configurable-paths

| ID | Question | Answer |
|----|----------|--------|
| Q66 | What exactly should be configurable? Just flows dir and session dir, or more? | Just the flows dir for now. Keep it simple. |
| Q67 | Should `flowr validate <file>` still accept a direct file path, or should it also support name-based lookup from the configured directory? | Direct file path only — no name-based lookup. The existing CLI interface stays unchanged. |
| Q68 | Should library functions (`load_flow_from_file`, `resolve_subflows`) use configured paths or stay explicit? | Library functions stay explicit — they take Path arguments. Configuration only affects the CLI layer. |
| Q69 | What should the exact defaults be for `flows_dir`? | SA decides — deferred. |
| Q70 | Should there be a `flowr config` CLI command? | Yes — `flowr config` prints current resolved configuration, showing each key, its value, and where it came from (default, pyproject.toml, or CLI flag). |
| Q71 | Should configuration be overridable at the command line? | Yes — `--flows-dir` CLI flag overrides the `pyproject.toml` value for a single invocation. |
| Q72 | Should the session directory be configurable too, or is that a separate tooling concern? | SA decides — session directory is deferred. |
| Q73 | Pre-mortem: what happens with misconfigured paths (non-existent dirs, relative vs. absolute)? | SA decides — misconfigured path handling is deferred. |

---

## 2026-04-26 — Session 4

Status: IN-PROGRESS

### Cross-cutting

| ID | Question | Answer |
|----|----------|--------|
| Q54 | Should the flow-definition-spec validation rules be extended to validate the new `conditions` field (e.g., unknown named references are MUST-level errors), or is that a separate concern? | Yes, extend the flow-definition-spec validation. Bump a minor version in the document. |
| Q55 | Should the `check` CLI subcommand display the resolved flat condition dict, the original named references, or both? | `check` displays the resolved flat condition dict. |
| Q56 | Should the Mermaid converter show named condition groups by name or as resolved conditions in diagram labels? | Mermaid shows resolved conditions (not named references). |
| Q57 | After inlining named references into a flat dict, does the closed evidence schema apply to the combined/resolved dict? | Yes, evidence must pass all the combined conditions for a state. |

### Feature: named-condition-groups

| ID | Question | Answer |
|----|----------|--------|
| Q58 | When a named reference and an inline dict in the same `when` list have overlapping keys, what happens? | Overlapping keys: later entries win. The `when` inline overrides the named reference's key. |
| Q59 | Can a named condition group reference another named group within the same `conditions` block? | No nesting — named groups cannot reference other named groups. Each group is a flat dict of condition expressions only. |
| Q60 | Can `when` contain multiple named references (e.g., `when: [reviewed, signed_off]`)? | Yes, `when` can contain multiple named references and additional inline dicts. |
| Q61 | What happens if a state has an empty `conditions` block (`conditions: {}`)? | `conditions` is an optional keyword — useful when repeating conditions, but not required on every state. An empty block is valid but has no effect. |
| Q62 | What happens if a named condition group has an empty dict as its value (e.g., `conditions: {noop: {}}`)? | Deferred to SA. |
| Q63 | Should the inlined result be visible to the user, or is inlining purely internal? | All conditions are flattened/combined. The user only sees the final list of conditions to verify. |
| Q64 | Should the validator check for unused named condition groups? | Deferred to SA. |
| Q65 | Pre-mortem: if a flow author writes `when: reviewed` (bare string), does it reference the named group? | `when` accepts three forms: bare dict (v1, unchanged), list (strings + inline dicts, AND-combined), and single string (shorthand for list with one named reference). `when: reviewed` is shorthand for `when: [reviewed]`. |

Status: COMPLETE


