# Domain Model: flowr

> Current understanding of the business domain.
> Updated by the Domain Expert when domain understanding evolves.
> This document captures what code cannot express: WHY entities exist, HOW aggregates are bounded, and WHAT business capabilities each context serves.
>
> **Evolving document:** Event Storming fills the Event Map, Aggregate Candidates, and Context Candidates sections (workshop draft). Domain Modeling then formalizes them into Entities, Relationships, and Aggregate Boundaries.

---

## Summary

flowr is a Python library and CLI for defining, validating, and visualizing non-deterministic state machine workflows in YAML. The core domain (Flow Definition) owns the specification, validation, and conversion of flow definitions. The CLI bounded context exposes these capabilities as subcommands and resolves flow names to file paths. The Session Tracking context manages persistent workflow state across CLI invocations, enabling agents and humans to resume where they left off without manual state tracking.

---

## Event Map

### Domain Events

| Event | Description | Trigger | Bounded Context |
|-------|-------------|---------|-----------------|
| `FlowDefinitionValidated` | A flow definition passed validation against the specification | `ValidateFlow` command | Flow Definition |
| `ViolationFound` | A conformance violation was detected in a flow definition | Validation process | Flow Definition |
| `SubflowResolved` | A subflow reference was resolved to a flow definition file | `LoadFlow` command | Flow Definition |
| `ConditionInlined` | A named condition group was inlined into a when clause | `LoadFlow` command | Flow Definition |
| `FlowConverted` | A flow definition was converted to Mermaid stateDiagram-v2 format | `ConvertFlow` command | Flow Definition |
| `TransitionChecked` | A transition was checked against a flow definition and evidence | `CheckTransition` command | CLI |
| `NextStatesListed` | Available next states were listed for a flow and current state | `ListNextStates` command | CLI |
| `TransitionAttempted` | A transition was attempted with trigger and evidence | `AttemptTransition` command | CLI |
| `FlowNameResolved` | A short flow name was resolved to a file path in the configured flows directory | `ResolveFlowName` command | CLI |
| `FlowNameNotFound` | A flow name was not found in the configured flows directory | `ResolveFlowName` command (no match) | CLI |
| `SessionInitialized` | A new session was created for a flow at its initial state | `InitSession` command | Session Tracking |
| `SessionStateChanged` | The current state in a session was updated | `SetSessionState` or `TransitionSession` command | Session Tracking |
| `SubflowPushed` | A parent flow+state was pushed onto the session stack when entering a subflow | `TransitionSession` command (subflow entry) | Session Tracking |
| `SubflowPopped` | A parent flow+state was popped from the session stack when exiting a subflow | `TransitionSession` command (subflow exit) | Session Tracking |
| `SessionLoaded` | An existing session was loaded from the session store | `LoadSession` command | Session Tracking |

### Commands

| Command | Description | Produces Event | Actor |
|---------|-------------|----------------|-------|
| `LoadFlow` | Load a flow definition from a YAML file, resolving subflows and inlining conditions | `SubflowResolved`, `ConditionInlined` | CLI User, Tool Author |
| `ValidateFlow` | Validate a flow definition against the specification | `FlowDefinitionValidated`, `ViolationFound` | CLI User, Tool Author |
| `ConvertFlow` | Convert a flow definition to Mermaid stateDiagram-v2 format | `FlowConverted` | CLI User, Tool Author |
| `CheckTransition` | Check whether a transition is valid from a given state with given evidence | `TransitionChecked` | CLI User, Agent |
| `ListNextStates` | List available next states for a flow and current state | `NextStatesListed` | CLI User, Agent |
| `AttemptTransition` | Attempt a transition with trigger and evidence | `TransitionAttempted` | CLI User, Agent |
| `ResolveFlowName` | Resolve a short flow name to a file path using the configured flows directory; falls back to name resolution only when the argument is not an existing file path | `FlowNameResolved` or `FlowNameNotFound` | CLI User, Agent |
| `InitSession` | Create a new session for a flow at its initial state | `SessionInitialized` | CLI User, Agent |
| `SetSessionState` | Update the current state in a session | `SessionStateChanged` | CLI User, Agent |
| `LoadSession` | Load an existing session from the session store | `SessionLoaded` | CLI User, Agent |
| `TransitionSession` | Transition a session to a new state: load session, validate transition, update session state, auto-update session file; push/pop subflow stack when entering/exiting subflows | `SessionStateChanged`, `SubflowPushed`, or `SubflowPopped` | CLI User, Agent |

### Read Models

| Read Model | Description | Consumes Event | Used By |
|------------|-------------|----------------|---------|
| `FlowDefinition` | The loaded flow domain object (Flow, States, Transitions, Conditions) | `SubflowResolved`, `ConditionInlined` | Validator, Mermaid Converter, CLI |
| `ValidationResult` | The result of validation: conformance level, violations | `FlowDefinitionValidated`, `ViolationFound` | CLI User, Tool Author |
| `MermaidDiagram` | The Mermaid stateDiagram-v2 text output | `FlowConverted` | CLI User, Tool Author |
| `AvailableTransitions` | The list of valid next states and their conditions | `TransitionChecked`, `NextStatesListed` | CLI User, Agent |
| `ResolvedFlowPath` | The resolved file path for a flow name | `FlowNameResolved` | CLI |
| `CurrentSession` | The current session state: flow name, current state, subflow stack, params | `SessionInitialized`, `SessionStateChanged`, `SubflowPushed`, `SubflowPopped`, `SessionLoaded` | CLI User, Agent |

---

## Context Candidates

> Filled during Event Storming. Formalized in Bounded Contexts section below by Domain Modeling.

| Candidate | Responsibility | Grouped Aggregates | Notes |
|-----------|---------------|--------------------|-------|
| Flow Definition | Define, validate, and convert non-deterministic state machine workflows in YAML | `Flow` | Core domain — the reason the product exists. Owns all domain types and invariants. |
| CLI | Expose the application as a command-line tool; parse args; resolve flow names; format and display results | `FlowNameResolution`, `Session` (shared with Session Tracking) | Driving adapter that depends on the domain. Flow name resolution is a CLI-layer concern — library functions take Path arguments. |
| Session Tracking | Manage persistent workflow state across CLI invocations; track subflow push/pop stack | `Session` | New context candidate. Has its own persistence (session YAML files), lifecycle (init, show, set-state), and invariants (atomic writes, stack consistency). Could be used by other delivery mechanisms in the future. |

---

## Aggregate Candidates

> Filled during Event Storming. Formalized in Aggregate Boundaries section below by Domain Modeling.

| Candidate | Events Grouped | Tentative Root Entity | Notes |
|-----------|---------------|-----------------------|-------|
| `Flow` | `FlowDefinitionValidated`, `ViolationFound`, `SubflowResolved`, `ConditionInlined`, `FlowConverted` | `Flow` | A Flow is the root entity of a flow definition; all States, Transitions, and Conditions belong to a single Flow and are loaded and validated together. |
| `FlowNameResolution` | `FlowNameResolved`, `FlowNameNotFound` | *(service, not an aggregate)* | Stateless resolution — no transactional consistency boundary needed. May become a domain service within the CLI context rather than a separate aggregate. |
| `Session` | `SessionInitialized`, `SessionStateChanged`, `SubflowPushed`, `SubflowPopped`, `SessionLoaded` | `Session` | A Session tracks workflow state across invocations. The stack must be consistent after every push/pop — this is the transactional invariant. Atomic writes prevent partial state corruption. |

---

## Bounded Contexts

| Context | Responsibility | Key Entities | Integration Points |
|---------|----------------|--------------|-------------------|
| Flow Definition | Define, validate, and convert non-deterministic state machine workflows in YAML | `Flow`, `State`, `Transition`, `GuardCondition`, `ConditionExpression`, `Param`, `ConformanceLevel`, `Violation`, `ValidationResult` | Loaded by CLI; consumed by Validator and Mermaid Converter |
| CLI | Expose the application as a command-line tool with subcommands; parse args; resolve flow names to file paths; format and display results | `CLIEntrypoint`, `FlowrConfig`, `FlowNameResolution` | Depends on Flow Definition (loads flows, validates, converts) and Session Tracking (session-aware commands) |
| Session Tracking | Manage persistent workflow state across CLI invocations; track subflow push/pop stack; provide session-aware command mode | `Session`, `SessionStackFrame`, `SessionStore` | Reads flow definitions from Flow Definition context; CLI dispatches session commands |

---

## Entities

| Name | Type | Description | Bounded Context | Aggregate Root? |
|------|------|-------------|-----------------|-----------------|
| `Flow` | Entity | Root entity of a flow definition; contains states, transitions, conditions, params, exits, and attrs | Flow Definition | Yes |
| `State` | Entity | A state within a flow; has an id, optional next mapping, optional subflow reference, optional attrs | Flow Definition | No |
| `Transition` | Entity | A trigger-to-target mapping within a state; may have guard conditions | Flow Definition | No |
| `GuardCondition` | Value Object | A dict of condition expressions (AND-combined) on a transition | Flow Definition | — |
| `ConditionExpression` | Value Object | A single condition expression string (e.g., `==true`, `>=80%`) | Flow Definition | — |
| `Param` | Value Object | A parameter declaration with optional default value | Flow Definition | — |
| `ConformanceLevel` | Value Object | MUST or SHOULD severity classification | Flow Definition | — |
| `Violation` | Value Object | A validation violation with severity, message, and location | Flow Definition | — |
| `ValidationResult` | Value Object | The result of validating a flow: list of violations | Flow Definition | — |
| `NamedConditionGroup` | Value Object | A named set of condition expressions defined at state level for reuse in when clauses | Flow Definition | — |
| `CLIEntrypoint` | Entity | The argparse-based CLI that dispatches subcommands and formats output | CLI | Yes |
| `FlowrConfig` | Value Object | Resolved configuration for the CLI (flows directory, session directory, etc.), read from `[tool.flowr]` in `pyproject.toml` and CLI flags | CLI | — |
| `FlowNameResolution` | Service | Resolves a short flow name to a file path using the configured flows directory; file paths take priority over name resolution | CLI | — |
| `ResolvedFlowPath` | Value Object | The resolved file path for a flow name, or an error indicating the name was not found | CLI | — |
| `Session` | Entity | A persistent record of workflow state (flow name, current state, subflow stack, params) that survives across CLI invocations | Session Tracking | Yes |
| `SessionStackFrame` | Value Object | A single frame in the session call stack, recording the parent flow name and the subflow wrapper state (the state with the `flow:` field whose `next` map defines exit resolution) | Session Tracking | — |
| `SessionStore` | Service | Persistence service for sessions; reads and writes session YAML files in `.flowr/sessions/` with atomic writes | Session Tracking | — |
| `CurrentSession` | Value Object | Read model representing the current session state for display | Session Tracking | — |

---

## Relationships

| Subject | Relation | Object | Cardinality | Notes |
|---------|----------|--------|-------------|-------|
| `Flow` | contains | `State` | 1:N | A flow has one or more states |
| `State` | contains | `Transition` | 1:N | A state has zero or more transitions in its next mapping |
| `Transition` | has | `GuardCondition` | 0..1:1 | A transition may have a when clause |
| `GuardCondition` | contains | `ConditionExpression` | 1:N | A when clause has one or more condition expressions |
| `State` | references | `NamedConditionGroup` | 0:N | A state may define named condition groups |
| `Transition` | references | `NamedConditionGroup` | 0:N | A when clause may reference named groups by name |
| `State` | invokes | `Flow` | 0..1:1 | A state with a flow field invokes a subflow |
| `Flow` | declares | `Exit` | 1:N | A flow declares exits that parent flows reference |
| `Flow` | declares | `Param` | 0:N | A flow may declare parameters |
| `CLIEntrypoint` | uses | `FlowNameResolution` | 1:1 | The CLI resolves flow names before loading |
| `CLIEntrypoint` | dispatches | `Session` | 1:0..1 | Session-aware commands use the current session |
| `FlowrConfig` | configures | `FlowNameResolution` | 1:1 | The resolved configuration provides the flows directory for name resolution |
| `Session` | references | `Flow` | N:1 | A session tracks the current flow by name |
| `Session` | contains | `SessionStackFrame` | 1:0..N | A session has a stack of parent contexts for subflows; each frame records the parent flow and the subflow wrapper state (the state with the `flow:` field) |
| `SessionStore` | persists | `Session` | 1:N | The session store manages all session files in `.flowr/sessions/` |
| `FlowNameResolution` | resolves | `Flow` | N:1 | Name resolution maps a flow name to a flow file path |

---

## Aggregate Boundaries

| Aggregate | Root Entity | Invariants | Bounded Context |
|-----------|-------------|------------|-----------------|
| `Flow` | `Flow` | A Flow must be self-consistent: all next targets resolve to valid states or exits, no cross-flow cycles exist, all condition references resolve, parent next keys match child exits | Flow Definition |
| `Session` | `Session` | (flow, state) must reference a valid state within the loaded flow; the subflow stack must be LIFO-consistent after every push/pop; session writes must be atomic (temp-file-then-rename) | Session Tracking |

---

## Changes

| Date | Source | Change | Reason |
|------|--------|--------|--------|
| 2026-05-01 | Event Storming: cli-flow-name-resolution, session-management | Added FlowNameResolved, FlowNameNotFound events; ResolveFlowName command; ResolvedFlowPath read model; FlowNameResolution service; CLI bounded context extended with flow name resolution | Interview IN_20260501_cli-flow-name-resolution — CLI resolves short flow names to file paths |
| 2026-05-01 | Event Storming: cli-flow-name-resolution, session-management | Added SessionInitialized, SessionStateChanged, SubflowPushed, SubflowPopped, SessionLoaded events; InitSession, SetSessionState, LoadSession, TransitionSession commands; CurrentSession read model; Session Tracking bounded context; Session aggregate extended with persistence and subflow stack | Interview IN_20260501_session-management — persistent session tracking with subflow push/pop |
| 2026-05-01 | Domain Modeling | Formalized Bounded Contexts, Entities, Relationships, and Aggregate Boundaries from event-storming candidates: added FlowrConfig (Value Object, CLI), SessionStackFrame (Value Object, Session Tracking), SessionStore (Service, Session Tracking); replaced SessionStack with SessionStackFrame; added FlowrConfig→FlowNameResolution and SessionStore→Session relationships; updated CLI and Session Tracking context key entities | Formalization of event-storming output into domain model |