Feature: Session Management (Extended)

  Extended session management features: `--session` flag on `next` and `check`
  commands, `session list` subcommand, `--format yaml|json` output option,
  error handling for missing sessions, and config-based session directory
  resolution.

  Depends on: session-management (core) — init, show, set-state, and
  session-aware transition must be implemented first.

  Status: ELICITING

  Rules (Business):
  - `session list` lists all sessions in the session store
  - `--format yaml|json` controls output format for session commands
  - `--session [<name>]` on `next` resolves flow and state from the session file
  - `--session [<name>]` on `check` resolves flow and state from the session file
  - Session show fails with a clear error if the session is not found
  - Session set-state fails with a clear error if the session is not found
  - `session init` resolves flow names via the configured `flows_dir`
  - The `sessions_dir` configuration key controls where session files are stored

  Constraints:
  - This feature does not add new subcommands beyond `session list`
  - `--format` applies only to `session show` and `session list`
  - `--session` on `next` and `check` is read-only — no session update

  Rule: Session-Aware Next
    As a flowr user
    I want to query next transitions from the session state
    So that I don't have to specify the flow and state every time

    @id:e7f8g9h0
    Example: Session-aware next resolves flow and state from session
      Given a session named default at feature-development-flow/planning
      When the user runs flowr next --session
      Then the CLI reads the flow and state from the session and shows available transitions

  Rule: Session-Aware Check
    As a flowr user
    I want to check state details from the session state
    So that I don't have to specify the flow and state every time

    @id:i1j2k3l4
    Example: Session-aware check resolves flow and state from session
      Given a session named default at feature-development-flow/planning
      When the user runs flowr check --session
      Then the CLI reads the flow and state from the session and shows state details

  Rule: Session List and Format
    As a flowr user
    I want to list all sessions and control output format
    So that I can see all my workflow sessions at a glance

    @id:q7r8s9t0_list
    Example: Session list shows all sessions
      Given sessions named default and my-session exist in the session store
      When the user runs flowr session list
      Then the CLI displays all sessions with name, flow, state, and updated_at

    @id:m3n4o5p6_json
    Example: Session show with JSON format
      Given a session named default at feature-development-flow/planning
      When the user runs flowr session show --format json
      Then the CLI displays the session state as JSON

  Rule: Error Handling
    As a flowr user
    I want clear error messages when sessions are not found or states are invalid
    So that I can diagnose and fix problems quickly

    @id:e5f6g7h8
    Example: Session init with explicit name
      Given a flow YAML at .flowr/flows/feature-development-flow.yaml
      When the user runs flowr session init feature-development-flow --name my-session
      Then the CLI creates a session file named my-session.yaml

    @id:g3h4i5j6
    Example: Session set-state fails if state not in flow
      Given a session at feature-development-flow/planning
      When the user runs flowr session set-state nonexistent-state
      Then the CLI prints an error indicating the state is not in the flow

    @id:y5z6a7b8_err
    Example: Session show fails if session not found
      Given no session named nonexistent
      When the user runs flowr session show --name nonexistent
      Then the CLI prints an error indicating the session was not found

    @id:k7l8m9n0_err
    Example: Session set-state fails if session not found
      Given no session named nonexistent
      When the user runs flowr session set-state planning --name nonexistent
      Then the CLI prints an error indicating the session was not found

  Rule: Config Resolution
    As a flowr user
    I want the session store directory to be configurable
    So that I can override the default location

    @id:m5n6o7p8
    Example: Session uses config default session directory
      Given a pyproject.toml with [tool.flowr] sessions_dir = ".flowr/sessions"
      When the user runs flowr session init feature-development-flow
      Then the CLI stores the session in .flowr/sessions/default.yaml

    @id:q9r0s1t2
    Example: Session init resolves flow name from config
      Given a pyproject.toml with [tool.flowr] flows_dir = ".flowr/flows"
      When the user runs flowr session init feature-development-flow
      Then the CLI resolves the flow name to .flowr/flows/feature-development-flow.yaml before creating the session