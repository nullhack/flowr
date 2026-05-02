Feature: Session Management (Core)

  The flowr CLI is currently stateless — each command requires the user to
  specify the flow file and state explicitly. Agents and humans must manually
  track which flow and state they are in, often by reading and writing session
  YAML files by hand.

  This feature adds core session management: `session init`, `session show`,
  and `session set-state` subcommands; a `--session` flag on `transition`
  that auto-resolves flow and state from a session file and auto-updates
  after mutations; and automatic subflow push/pop tracking in session-aware
  transitions.

  The library layer (`Session`, `SessionStackFrame` dataclasses) already exists
  in `flowr/domain/session.py`. The `SessionStore` Protocol and `YamlSessionStore`
  implementation are defined in the technical design. Session persistence uses
  atomic writes (temp-file-then-rename).

  Status: BASELINED (2026-05-01)

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-01 S7 | Q1–Q13 | Created: session init/show/set-state subcommands, --session flag on transition, auto-write after mutation, push/pop for subflows, atomic writes, no params on init, last-write-wins concurrency |

  Rules (Business):
  - `session init <flow>` creates a new session at the flow's initial state and persists it to the session store
  - `session show` displays the current session's flow, state, stack, and metadata
  - `session set-state <state>` updates the current state in the session
  - `--session [<name>]` on `transition` resolves flow and state from the session file instead of requiring positional arguments
  - After a session-aware `transition`, the session file is auto-updated with the new state
  - If a session-aware transition enters a subflow, the parent flow+state is pushed onto the session stack
  - If a session-aware transition exits a subflow, the parent flow+state is popped from the session stack
  - Session files are persisted using atomic writes (temp-file-then-rename)
  - Commands without `--session` behave identically to the current version (backward compatible)
  - `session init` does NOT accept params; params are reserved for future use

  Constraints:
  - Session management is a CLI-layer concern; the domain layer provides dataclasses only
  - `--session` is opt-in; all existing commands work without it
  - No file locking or concurrency control; last-write-wins is acceptable

  Rule: Session Init
    As a flowr user
    I want to initialize a session for a flow
    So that I can track my progress through a workflow

    @id:a1b2c3d4
    Example: Session init creates a session at the flow's initial state
      Given a flow YAML at .flowr/flows/feature-development-flow.yaml
      When the user runs flowr session init feature-development-flow
      Then the CLI creates a session file with the flow name, the initial state, and a default name

    @id:i9j0k1l2
    Example: Session init fails if session already exists
      Given a session named default already exists
      When the user runs flowr session init feature-development-flow
      Then the CLI prints an error indicating the session already exists

  Rule: Session Show
    As a flowr user
    I want to see the current session state
    So that I know where I am in the workflow

    @id:m3n4o5p6
    Example: Session show displays current session state
      Given a session named default at feature-development-flow/planning
      When the user runs flowr session show
      Then the CLI displays the flow, state, stack, and timestamps

    @id:u1v2w3x4
    Example: Session show displays subflow stack
      Given a session with a subflow stack containing one frame
      When the user runs flowr session show
      Then the CLI displays the stack entries showing parent flow and state

  Rule: Session Set-State
    As a flowr user
    I want to manually update the session state
    So that I can correct or skip to a specific state

    @id:c9d0e1f2
    Example: Session set-state updates the current state
      Given a session named default at feature-development-flow/planning
      When the user runs flowr session set-state architecture
      Then the CLI updates the session state to architecture and persists it

    Rule: Session-Aware Transition
    As a flowr user
    I want to transition within a session so that the session is auto-updated
    So that I don't have to manually update the session file after every transition

    @id:o1p2q3r4
    Example: Session-aware transition updates session state
      Given a session named default at feature-development-flow/planning
      When the user runs flowr transition --session architecture
      Then the CLI reads the flow and state from the session, performs the transition, and auto-updates the session

    @id:s5t6u7v8
    Example: Session-aware transition pushes stack on subflow entry
      Given a session at feature-development-flow/step-1-scope and the transition enters a subflow
      When the user runs flowr transition --session some-trigger
      Then the CLI pushes the parent flow+state onto the session stack and updates the state to the subflow's initial state

    @id:w9x0y1z2
    Example: Session-aware transition pops stack on subflow exit
      Given a session with a stack frame and the transition exits the subflow
      When the user runs flowr transition --session complete
      Then the CLI pops the stack frame and restores the parent flow+state