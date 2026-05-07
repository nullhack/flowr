Feature: Subflow Transition Overhaul

  The subflow mechanism (push/pop stack for nested flows) is completely
  non-functional for real flows due to two critical bugs in path resolution
  and exit handling. Additionally, the `next` command hides critical
  navigation information — trigger names, guarded transitions, and evidence
  requirements — making autonomous agent navigation impossible.

  This feature fixes the subflow mechanism, enhances `next` to show the
  complete navigation picture, and improves session command robustness.

  Depends on: session-management (core), session-management-extended.

  Status: ELICITING

  Rules (Business):
  - Flow references without `.yaml` extension are resolved by appending `.yaml` if the bare path doesn't exist
  - Subflow exit resolves through the parent flow's transition map, not by using the exit name directly
  - Subflow chaining: after exiting one subflow, if the resolved target enters another subflow, the stack is pushed again
  - `session init` auto-enters the initial subflow if the first state has a `flow:` field
  - `next` always shows ALL transitions including blocked/guarded ones, with status markers
  - `next` output shows trigger→target mapping with inline condition requirements
  - `next` JSON output uses `transitions` array of objects with `trigger`, `target`, `status`, `conditions`
  - `check --session <target>` correctly shows transition conditions
  - `states --session` and `validate --session` resolve the current flow from session

  Constraints:
  - Non-session commands remain backward compatible
  - `next` JSON output is a breaking change: `next` array of strings replaced with `transitions` array of objects
  - Domain layer (Session, SessionStackFrame) changes are minimal — fixes are in CLI/transition logic

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q1 | Should `next` show all transitions or require `--all` flag? | Resolved | Always show all — agents need the full picture |
  | Q2 | Should `next` JSON preserve backward compatibility? | Resolved | No — clean break, replace `next` array with `transitions` objects |
  | Q3 | Should `set-state` support crossing flow boundaries? | Open | Phase 3 — may add `--flow` flag for recovery scenarios |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-05 S1 | Q1-Q3 | Created: subflow resolution, exit handling, next overhaul, session robustness |

  Rule: Subflow Path Resolution
    As a flowr user
    I want flow references without file extensions to resolve correctly
    So that I can use clean flow names in YAML definitions

    @id:sf-001
    Example: Flow reference without .yaml extension resolves correctly
      Given a flow YAML with `flow: discovery-flow` referencing a file `discovery-flow.yaml`
      When the CLI resolves subflows
      Then the subflow is loaded successfully

    @id:sf-002
    Example: Flow reference with .yaml extension still works
      Given a flow YAML with `flow: child.yaml` referencing a file `child.yaml`
      When the CLI resolves subflows
      Then the subflow is loaded successfully

  Rule: Subflow Exit Resolution
    As a flowr user
    I want subflow exits to correctly resolve through the parent flow's transitions
    So that my session lands on the correct next state after completing a subflow

    @id:sf-003
    Example: Subflow exit resolves parent transition target
      Given a session inside discovery-flow with stack frame pointing to main-flow/discovery
      And discovery-flow exits with `complete`
      And main-flow/discovery maps `complete → architecture`
      When the user transitions with the exit trigger
      Then the session pops the stack and lands at main-flow/architecture

    @id:sf-004
    Example: Subflow chaining enters next subflow after exit
      Given a session exiting discovery-flow back to main-flow
      And the resolved target `architecture` has `flow: architecture-flow`
      When the subflow exit resolves to architecture
      Then the session pushes a new stack frame and enters architecture-flow

    @id:sf-005
    Example: Subflow exit with invalid parent state produces error
      Given a session inside a subflow with a corrupted stack frame
      When the subflow exit cannot find the parent state
      Then the CLI prints a clear error indicating the parent state is invalid

  Rule: Session Init Enters Subflow
    As a flowr user
    I want session init to automatically enter the initial subflow
    So that I can start working immediately without an extra transition step

    @id:sf-006
    Example: Session init auto-enters subflow when initial state has flow field
      Given a flow whose initial state has `flow: discovery-flow`
      When the user runs flowr session init main-flow
      Then the session is created inside discovery-flow with a stack frame pointing to main-flow

    @id:sf-007
    Example: Session init without subflow works as before
      Given a flow whose initial state has no `flow:` field
      When the user runs flowr session init simple-flow
      Then the session is created at the initial state with no stack

  Rule: Next Shows Full Transition Map
    As a flowr user
    I want to see all transitions with trigger names, targets, and condition requirements
    So that I can navigate without reading raw YAML files

    @id:sf-008
    Example: Next shows trigger→target mapping for all transitions
      Given a session at a state with transitions `needs_full_discovery → event-storming`, `needs_scope_only → scope-boundary`
      When the user runs flowr next --session
      Then the output shows each trigger name alongside its target state

    @id:sf-009
    Example: Next shows blocked guarded transitions with condition hints
      Given a session at a state with a guarded transition requiring `committed_to_main_locally=verified`
      When the user runs flowr next --session without evidence
      Then the blocked transition appears with a marker showing the required evidence

    @id:sf-010
    Example: Next shows passing guarded transitions
      Given a session at a state with a guarded transition requiring `committed_to_main_locally=verified`
      When the user runs flowr next --session --evidence committed_to_main_locally=verified
      Then the transition appears as passing/open

    @id:sf-011
    Example: Next JSON output uses transitions array with full details
      Given a session at a state with transitions
      When the user runs flowr next --session --json
      Then the output contains a `transitions` array where each entry has `trigger`, `target`, `status`, and `conditions`

  Rule: Check Session Shows Conditions
    As a flowr user
    I want to check transition conditions from session mode
    So that I know exactly what evidence to provide

    @id:sf-012
    Example: Check session with target shows transition conditions
      Given a session at a state with a guarded transition
      When the user runs flowr check --session <trigger-name>
      Then the output shows the conditions required for that transition

  Rule: Session-Aware States and Validate
    As a flowr user
    I want to list states and validate the current flow from session
    So that I can inspect my current (sub)flow context without specifying the flow name

    @id:sf-013
    Example: States command with --session lists current flow's states
      Given a session inside architecture-flow
      When the user runs flowr states --session
      Then the output lists all states in architecture-flow

    @id:sf-014
    Example: Validate command with --session validates current flow
      Given a session inside architecture-flow
      When the user runs flowr validate --session
      Then the output validates architecture-flow
