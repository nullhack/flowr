# Glossary: flowr

> Living glossary of domain terms used in this project.
> Written and maintained by the product-owner during Step 1 discovery.
> Append-only: never edit or remove past entries. If a term changes, mark it retired in favour of the new entry and write a new entry.
> Code and tests take precedence over this glossary — if they diverge, refactor the code, not this file.

---

## Entry Format

```
## <Term>

**Definition:** <one sentence — genus + differentia: "A [category] that [distinguishes it from others in that category]">

**Aliases:** <deprecated synonyms the team should stop using, or "none">

**Example:** <one sentence showing the term in use in this project; optional but encouraged>

**Source:** <feature stem or discovery session date>
```

Entries are sorted alphabetically.

---

## Evidence

**Definition:** A key-value dict provided by an actor when triggering a transition, whose keys must exactly match the guard condition's `when` keys (closed schema — no extra or missing keys allowed).

**Aliases:** evidence dict, transition evidence

**Example:** "A guard condition `when: {all_tests_pass: "==true"}` requires evidence `{all_tests_pass: "true"}` — any other key is rejected."

**Source:** 2026-04-26 — Session 2 (Q25); Issue #3

---

## Exit

**Definition:** A named element of a flow's contract that allows a parent flow to receive a transition when the child flow completes a path; exits are always required and declared at flow level.

**Aliases:** subflow exit, flow exit

**Example:** "The `scope-cycle` flow declares `exits: [complete, blocked]` — a parent flow references these names in its `next` mapping to handle subflow completion."

**Source:** 2026-04-26 — Session 2 (Q22, Q30); Issue #3

---

## Flows Directory

**Definition:** The configurable directory containing flow definition YAML files; specified via the `flows_dir` key in `[tool.flowr]` configuration or the `--flows-dir` CLI flag.

**Aliases:** flows_dir, flow definitions directory

**Example:** "Setting `flows_dir = "workflows"` in `[tool.flowr]` causes the CLI to resolve subflow references relative to the `workflows/` directory."

**Source:** 2026-04-26 — Session 5 (Q66–Q73); feature `configurable-paths`

---

## Flow Definition

**Definition:** A YAML document that describes a non-deterministic state machine workflow, conforming to the flow specification format with top-level fields `flow`, `version`, `params`, `exits`, `attrs`, and `states`.

**Aliases:** flow YAML, flow file

**Example:** "The file `docs/flows/feature-flow.yaml` is a flow definition that describes the five-step feature delivery workflow."

**Source:** 2026-04-26 — Session 2 (Q13, Q30); Issue #3

---

## Flow Specification

**Definition:** The formal specification document that defines the YAML format, validation rules, and conformance levels (MUST/SHOULD) for flow definitions, independent of any specific implementation.

**Aliases:** spec, specification format

**Example:** "The flow specification defines that state-level attrs replace flow-level attrs entirely — any conforming validator must enforce this rule."

**Source:** 2026-04-26 — Session 2 (Q14, Q33)

---

## Fuzzy Match

**Definition:** The `~=` condition operator that performs approximate numeric matching; passes if the evidence value is within 5% of the condition value after numeric extraction.

**Aliases:** approximate match, ~= operator

**Example:** "The condition `~=100` with evidence `97` passes because |97 - 100| / 100 = 0.03 ≤ 0.05 — within 5% tolerance."

**Source:** 2026-04-26 — Session 2 (Q20); ADR-2026-04-26-fuzzy-match-algorithm

---

## Guard Condition

**Definition:** A `when` clause on a transition that specifies conditions which must all be satisfied (AND-combined) for the transition to fire; conditions use operators like `==`, `!=`, `>=`, `<=`, `>`, `<`, and `~=`.

**Aliases:** when clause, transition guard

**Example:** "The transition `complete: { to: step-5, when: { all_tests_pass: "==true" } }` fires only when evidence contains `all_tests_pass: "true"`."

**Source:** 2026-04-26 — Session 2 (Q25); Issue #3

---

## CLI Subcommand

**Definition:** A top-level command in the flowr CLI that operates on flow definitions; each subcommand (validate, states, check, next, transition, mermaid, image) is a separate one-shot invocation.

**Aliases:** CLI command, subcommand

**Example:** "`flowr validate myflow.yaml` checks the flow definition against the specification; `flowr states myflow.yaml` lists all states in the flow."

**Source:** 2026-04-26 — Session 3 (Q34)

---

## Flow Loading

**Definition:** The process of reading a root flow YAML file and recursively resolving subflow references to build a complete set of flow definitions for CLI operations.

**Aliases:** flow resolution, subflow loading

**Example:** "When the CLI loads `feature-flow.yaml`, it automatically finds and loads `scope-cycle.yaml` referenced by the `flow: scope-cycle` field in a state."

**Source:** 2026-04-26 — Session 3 (Q43)

---

## Acceptance Criteria

**Definition:** A set of conditions that a feature must satisfy before the product-owner considers it complete.

**Aliases:** Definition of Done (different concept — do not conflate), exit criteria

**Example:** "The CLI entrypoint acceptance criterion states: given the package is installed, when the user runs `python -m flowr --version`, then the output contains the version string from package metadata."

**Source:** template — BDD practice (Gherkin `Example:` blocks with `@id` tags)

---

## Attrs

**Definition:** An opaque dict at flow level or state level that carries project-specific data; state-level attrs replace flow-level attrs entirely (no merge, no deep merge).

**Aliases:** attributes, flow attrs, state attrs

**Example:** "A flow defines `attrs: {agents: {idle: product-owner}}`; a state defines `attrs: {retry: true}` — the state's attrs completely replace the flow's attrs for that state."

**Source:** 2026-04-26 — Session 2 (Q19)

---

## ADR (Architecture Decision Record)

**Definition:** A short document that records a significant architectural decision — the context that triggered it, the self-interview questions and answers that led to the decision, the alternatives considered, and the consequences. One ADR can group multiple related Q&A pairs that converge on a single decision.

**Aliases:** decision log entry, design decision record

**Example:** "ADR-2026-04-22-cli-parser-library records why the team chose argparse over click for the CLI skeleton, including the self-interview questions the SA asked before stakeholder validation."

**Source:** template — Nygard (2011), MADR format

---

## Agent

**Definition:** An AI assistant assigned a specific role in the development workflow, operating within defined boundaries and producing defined outputs.

**Aliases:** AI agent, LLM agent, assistant

**Example:** "The product-owner agent interviews the stakeholder and writes `.feature` files; the software-engineer agent implements the tests and production code."

**Source:** template — this project's workflow

---

## BDD (Behaviour-Driven Development)

**Definition:** A collaborative software development practice in which acceptance criteria are written as concrete examples of system behaviour, expressed in a structured natural language understood by both stakeholders and developers.

**Aliases:** Behaviour-Driven Development, Behavior-Driven Development (US spelling)

**Example:** "The team uses BDD to write Gherkin `Example:` blocks that become the executable specification for each feature."

**Source:** template — North (2006) BDD origin paper

---

## Backlog

**Definition:** The ordered collection of features that have been discovered and baselined but not yet started.

**Aliases:** feature backlog, product backlog

**Example:** "The product-owner moves `cli-entrypoint.feature` from `backlog/` to `in-progress/` when the team is ready to begin implementation."

**Source:** template — this project's workflow

---

## Bounded Context

**Definition:** A boundary within a domain model inside which a particular ubiquitous language is internally consistent and unambiguous.

**Aliases:** context boundary, model boundary

**Example:** "In a retail system, 'Product' means a catalogue entry in the browsing context but means a fulfilment line item in the shipping context — they are different concepts in different bounded contexts."

**Source:** template — Evans (2003) DDD; Fowler (2014) BoundedContext bliki

---

## CLI Entrypoint

**Definition:** The `flowr/__main__.py` module that wires the application's command-line interface, exposing `--help` and `--version` flags via Python's stdlib `argparse`.

**Aliases:** entry point, main module, CLI entry

**Example:** "Running `python -m flowr --version` invokes the CLI entrypoint and prints `flowr 0.1`."

**Source:** 2026-04-22 — Session 1; feature `cli-entrypoint`

---

## Conformance

**Definition:** A classification of validation rule severity into two levels: MUST (required for all conforming implementations) and SHOULD (recommended but not mandatory).

**Aliases:** conformance level, compliance level

**Example:** "The specification says a conforming validator MUST reject ambiguous next-target collisions and SHOULD warn about unused exits."

**Source:** 2026-04-26 — Session 2 (Q26)

---

## Cross-flow Cycle

**Definition:** A cycle that spans two or more flows via subflow invocation (parent→child→parent), which is forbidden by the specification.

**Aliases:** inter-flow cycle, parent-child cycle

**Example:** "If flow A invokes flow B as a subflow, and flow B's exit targets a state in flow A that re-enters flow B, that is a cross-flow cycle — a validation error."

**Source:** 2026-04-26 — Session 2 (Q23)

---

## DDD (Domain-Driven Design)

**Definition:** A software design approach that centres the codebase around an explicit model of the business domain, using the same language in code, tests, and stakeholder conversations.

**Aliases:** Domain-Driven Design

**Example:** "Following DDD, the team names the Python class `Invoice` because the accountant calls it an invoice — not `BillingDocument` or `PaymentRecord`."

**Source:** template — Evans (2003) Domain-Driven Design; Evans (2015) DDD Reference

---

## Demonstration Feature

**Definition:** The single working feature that ships with the template to show engineers the full five-step delivery workflow end-to-end before they build their own features.

**Aliases:** demo feature, starter feature

**Example:** "The `cli-entrypoint` feature is the demonstration feature — it implements `--help` and `--version` flags and is delivered through all five workflow steps."

**Source:** 2026-04-22 — Session 1 (Q8, Q9)

---

## Domain Event

**Definition:** A record of something that happened in the domain that domain experts care about, expressed as a past-tense verb phrase.

**Aliases:** event, business event

**Example:** "`OrderPlaced`, `VersionDisplayed`, and `ReportGenerated` are domain events — they record facts that occurred, not commands to be executed."

**Source:** template — Vernon (2013) Implementing DDD

---

## Feature

**Definition:** A unit of user-visible functionality described by a `.feature` file containing a title, narrative, rules, and acceptance criteria examples.

**Aliases:** story, user story (broader concept — a feature here is a Gherkin file)

**Example:** "The `cli-entrypoint` feature covers all behaviour related to the application's command-line interface."

**Source:** template — this project's workflow

---

## Gherkin

**Definition:** A structured plain-English syntax for writing acceptance criteria using `Feature`, `Rule`, `Example`, `Given`, `When`, and `Then` keywords.

**Aliases:** Cucumber syntax, BDD syntax

**Example:** "`Given the application package is installed`, `When the user runs python -m flowr --version`, `Then the output contains the version string` is a Gherkin example."

**Source:** template — Cucumber project; North (2006) BDD origin

---

## Next Target Collision

**Definition:** A validation error that occurs when a `next` target matches both a state id and an exit name within the same flow, creating an ambiguous reference that cannot be resolved.

**Aliases:** target collision, ambiguous target

**Example:** "If a flow has both a state with `id: complete` and an exit named `complete`, any `next` targeting `complete` is a next-target collision and must be rejected at load time."

**Source:** 2026-04-26 — Session 2 (Q22)

---

## Numeric Extraction

**Definition:** The process of stripping non-numeric suffixes (such as `%`) from both condition values and evidence values before performing numeric comparison.

**Aliases:** numeric stripping, value extraction

**Example:** "The condition `>=80%` with evidence `75%` extracts 80 and 75 respectively, then compares 75 >= 80 → false."

**Source:** 2026-04-26 — Session 2 (Q21)

---

## Package Metadata

**Definition:** The runtime-accessible project information (name, version, description, author) stored in `pyproject.toml` and read at runtime via Python's `importlib.metadata` stdlib module.

**Aliases:** project metadata, distribution metadata

**Example:** "`importlib.metadata.version('flowr')` returns `0.1` at runtime, matching the `version` field in `pyproject.toml`."

**Source:** 2026-04-22 — Session 1 (Q10, Q11); feature `cli-entrypoint`

---

## Params

**Definition:** Declarations of parameter names a flow expects, with optional default values; a param without a default is required and causes a validation error if missing when the flow is invoked.

**Aliases:** flow parameters, flow params

**Example:** "A flow declares `params: [feature_slug, branch_name]` — both are required. A flow declaring `params: [{name: verbose, default: false}]` makes `verbose` optional with a default of `false`."

**Source:** 2026-04-26 — Session 2 (Q24); Issue #3

---

## Product Owner (PO)

**Definition:** The agent responsible for discovering requirements, writing acceptance criteria, and deciding whether delivered features meet stakeholder needs.

**Aliases:** PO

**Example:** "The product-owner interviews the stakeholder, writes `.feature` files, and either accepts or rejects delivered features at Step 5."

**Source:** template — this project's workflow (adapted from Scrum PO role)

---

## Skill

**Definition:** A markdown file loaded on demand that provides an agent with specialised instructions for a specific task.

**Aliases:** prompt skill, agent skill

**Example:** "The software-engineer loads the `implement` skill at the start of Step 3 to receive TDD loop instructions."

**Source:** template — this project's workflow

---

## Software Engineer (SE)

**Definition:** The agent responsible for writing tests, implementing production code, and maintaining the git history during the TDD loop.

**Aliases:** SE, developer, implementer

**Example:** "The software-engineer runs `uv run task test-fast` after every code change to verify the test suite stays green."

**Source:** template — this project's workflow

---

## Stakeholder

**Definition:** The human who owns the problem being solved, provides domain knowledge, and has final authority over whether delivered features meet their needs.

**Aliases:** user, domain expert, customer, product manager

**Example:** "The stakeholder answered Q11 by choosing Option C — `--help` + `--version` combined — as the demonstration feature."

**Source:** template — requirements-elicitation practice

---

## Subflow

**Definition:** A flow invoked by another flow via the `flow` field on a state, using a call-stack mechanism with isolated context; the parent's `next` keys must match the child's `exits` list exactly.

**Aliases:** child flow, invoked flow

**Example:** "The state `step-1-scope` declares `flow: scope-cycle`, making it a subflow invocation — when scope-cycle exits, the parent transitions according to its `next` mapping."

**Source:** 2026-04-26 — Session 2 (Q23, Q30); Issue #3

---

## System Architect (SA)

**Definition:** The agent responsible for translating accepted requirements into an architectural design, writing domain stubs, recording architectural decisions, and verifying implementation against the design.

**Aliases:** SA, architect, technical lead

**Example:** "The system-architect reads `cli-entrypoint.feature`, writes domain stubs in `flowr/__main__.py`, and records the argparse decision as an ADR."

**Source:** template — this project's workflow

---

## Trigger

**Definition:** A transition name sent by an actor to attempt a state change, accompanied by evidence matching the guard condition's `when` keys.

**Aliases:** transition trigger, event

**Example:** "An actor sends trigger `approved` with evidence `{review_approved: "true"}` to move from state `step-4-ready` to state `step-5-ready`."

**Source:** 2026-04-26 — Session 2 (Q25); Issue #3

---

## TDD (Test-Driven Development)

**Definition:** A development practice in which a failing test is written before any production code, the minimum code needed to pass that test is written, and then the code is refactored while keeping the test green.

**Aliases:** Test-Driven Development, test-first development

**Example:** "Following TDD, the software-engineer writes a failing `test_cli_entrypoint_c1a2b3d4` test, then writes only enough production code to make it pass."

**Source:** template — Beck (2002) Test-Driven Development by Example

---

## Ubiquitous Language

**Definition:** A shared vocabulary built from domain-expert terms that is used consistently in all conversation, documentation, and code within a bounded context.

**Aliases:** domain language, shared language, common language

**Example:** "Because the stakeholder says 'help flag', the code uses `--help` as the argument name — the ubiquitous language ensures no translation layer exists between domain expert and code."

**Source:** template — Evans (2003) DDD; Evans (2015) DDD Reference

---

## Within-flow Cycle

**Definition:** A cycle contained within a single flow (e.g., `idle → step-1-scope → blocked → idle`), which is allowed by the specification.

**Aliases:** intra-flow cycle, self-cycle

**Example:** "The feature-flow definition contains a within-flow cycle: `idle → step-1-scope → blocked → idle` — this is valid and common in state machine workflows."

**Source:** 2026-04-26 — Session 2 (Q23)

---

## Configuration

**Definition:** A `[tool.flowr]` section in `pyproject.toml` that provides runtime settings for the flowr CLI, such as the directory containing flow definition files.

**Aliases:** tool.flowr, flowr config, CLI configuration

**Example:** "A `[tool.flowr]` section with `flows_dir = "flows"` tells the CLI to look for flow definitions in the `flows/` directory instead of the default."

**Source:** 2026-04-26 — Session 5 (Q66–Q73); feature `configurable-paths`

---

## Condition Inlining

**Definition:** The load-time process of resolving named condition references in a `when` clause into a single flat dict of condition expressions, producing the combined evidence schema that the closed-evidence rule validates against.

**Aliases:** condition resolution, inlining

**Example:** "A `when: [reviewed, {score: ">=80"}]` where `reviewed` resolves to `{approved: "==true", signed_off: "==true"}` inlines to `{approved: "==true", signed_off: "==true", score: ">=80"}` — the closed evidence schema then requires all three keys."

**Source:** 2026-04-26 — Session 4 (Q57, Q63); Issue #2

---

## Condition Reference

**Definition:** A string in a `when` list that names a key in the same state's `conditions` block; resolved by inlining the named group's condition expressions at load time.

**Aliases:** named reference, condition name

**Example:** "In `when: [reviewed, {retry_count: "<3"}]`, the string `reviewed` is a condition reference that resolves to the condition group defined in the state's `conditions` block."

**Source:** 2026-04-26 — Session 4 (Q58, Q60, Q65); Issue #2

---

## Named Condition Group

**Definition:** A named entry in a state's `conditions` dict that maps a group name to a flat dict of condition expressions (same syntax as `when` values), allowing multiple transitions to reference the same set of conditions by name.

**Aliases:** condition group, named group

**Example:** "A state defines `conditions: {reviewed: {approved: "==true", signed_off: "==true"}}` — transitions can then use `when: reviewed` or `when: [reviewed]` instead of repeating the same conditions inline."

**Source:** 2026-04-26 — Session 4 (Q58–Q65); Issue #2

---

## WIP (Work In Progress)

**Definition:** The count of features currently being actively developed; this project enforces a WIP limit of one feature at a time.

**Aliases:** work in progress, in-flight work

**Example:** "If `docs/features/in-progress/` already contains a `.feature` file, the WIP limit is reached and no new feature may start until that one is accepted."

**Source:** template — Kanban WIP limit principle

---
