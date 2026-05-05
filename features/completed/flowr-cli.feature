Feature: Flowr CLI

  One-shot CLI for interacting with flow definitions. Provides seven subcommands
  (validate, states, check, next, transition, mermaid, image) that operate on a
  root flow YAML file and auto-resolve subflow references. Output is
  human-readable text by default with a --json flag for machine-readable output.
  Transitions are stateless — each command invocation computes and prints the
  result without persisting session state.

  Status: BASELINED (2026-04-26)

  Rules (Business):
  - All subcommands accept a root flow YAML file path and auto-resolve subflow
    references from it
  - Output is human-readable text by default; --json flag produces
    machine-readable JSON output
  - Transitions are stateless — no session file is created or updated
  - When a transition leads to a subflow state, the CLI enters the subflow at
    its first (initial) state
  - The `check` command serves two purposes depending on arguments: with state
    only it shows state details; with state + target it shows required
    conditions for that transition

  Constraints:
  - No interactive mode — each command is a separate invocation
  - Image rendering deferred to v2 (ADR-2026-04-26-image-rendering-deferral)
  - Evidence input via --evidence key=value and --evidence-json (ADR-2026-04-26-cli-io-convention)
  - Subflow file lookup via relative path from root flow directory (ADR-2026-04-26-subflow-resolution)
  - Subflow output as <flow-name>/<first-state-id> (ADR-2026-04-26-subflow-resolution)
  - Exit codes: 0=success, 1=fail, 2=usage error (ADR-2026-04-26-cli-io-convention)
  - Validate always lists all violations (ADR-2026-04-26-cli-io-convention)

  ## Frozen Examples Rule

  After a feature is BASELINED, all `Example:` blocks are immutable. Changes require
  `@deprecated` on the old Example (preserving the original @id) and a new Example
  with a new @id. This prevents scope creep and maintains traceability.

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q38 | Should image call an external tool or output Mermaid text? | Resolved | Deferred to v2 (ADR-2026-04-26-image-rendering-deferral) |
  | Q41 | How should evidence be provided to next and transition? | Resolved | --evidence key=value and --evidence-json (ADR-2026-04-26-cli-io-convention) |
  | Q46 | How should CLI find subflow files? | Resolved | Relative path from root flow directory (ADR-2026-04-26-subflow-resolution) |
  | Q49 | What should validate output? | Resolved | All violations listed; MUST errors and SHOULD warnings (ADR-2026-04-26-cli-io-convention) |
  | Q51 | When transition enters subflow, should output show subflow name + first state? | Resolved | Output as <flow-name>/<first-state-id> (ADR-2026-04-26-subflow-resolution) |
  | Q52 | Should CLI commands use exit codes? | Resolved | 0=success, 1=fail, 2=usage error (ADR-2026-04-26-cli-io-convention) |
  | Q53 | Is the primary input a single YAML file path? | Resolved | Yes, positional path argument (ADR-2026-04-26-cli-io-convention) |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-04-26 S3 | Q34–Q53 | Created: 7 one-shot subcommands (validate, states, check, next, transition, mermaid, image); text default, --json flag; stateless transitions; 8 SA-deferred decisions (evidence format, subflow lookup, subflow output, exit codes, validate output, image implementation) |

  Rule: Validate Command
    As a developer
    I want to validate a flow definition file against the specification
    So that I can catch errors before using the flow

    @id:f82e43f3
    Example: Valid flow passes validation
      Given a flow definition file that conforms to the specification
      When the developer runs the validate command on that file
      Then the output indicates the flow is valid

    @id:e60ea5d5
    Example: Flow with MUST violation fails validation
      Given a flow definition file missing required fields
      When the developer runs the validate command on that file
      Then the output lists at least one MUST-level violation

    @id:c74ff68e
    Example: Flow with SHOULD warning passes with warnings
      Given a flow definition file with a SHOULD-level issue
      When the developer runs the validate command on that file
      Then the output lists at least one SHOULD-level warning

    @id:25479a5b
    Example: Validate with --json outputs machine-readable results
      Given a flow definition file with violations
      When the developer runs the validate command with --json on that file
      Then the output is valid JSON containing the violation details

  Rule: States Command
    As a developer
    I want to list all states in a flow definition
    So that I can see the overall structure at a glance

    @id:2faa93a6
    Example: States lists all state ids in a flow
      Given a flow definition with three states named idle, working, done
      When the developer runs the states command on that file
      Then the output contains all three state ids

    @id:9b7eba0c
    Example: States with --json outputs a JSON array
      Given a flow definition with multiple states
      When the developer runs the states command with --json
      Then the output is a valid JSON array of state ids

  Rule: Check State
    As a developer
    I want to inspect a specific state's details
    So that I can understand its attrs, transitions, and subflow reference

    @id:92de4c71
    Example: Check state shows attrs and transitions
      Given a flow definition with a state that has attrs and transitions
      When the developer runs the check command for that state
      Then the output includes the state's attrs and available transitions

    @id:155a7306
    Example: Check state with subflow reference shows the subflow name
      Given a flow definition with a state that references a subflow
      When the developer runs the check command for that state
      Then the output includes the referenced subflow name

    @id:0cf36941
    Example: Check state with --json outputs structured data
      Given a flow definition with a state
      When the developer runs the check command with --json for that state
      Then the output is valid JSON containing the state details

    @id:e40ccf95
    Example: Check non-existent state reports error
      Given a flow definition
      When the developer runs the check command for a state that does not exist
      Then the output indicates the state was not found

  Rule: Check Conditions
    As a developer
    I want to see the conditions required for a specific transition
    So that I know what evidence I need to provide to trigger it

    @id:d9d7f5d7
    Example: Check conditions for a guarded transition
      Given a flow definition with a state that has a guarded transition
      When the developer runs the check command for that state and target
      Then the output shows the guard condition's evidence keys and operators

    @id:3d4c9d59
    Example: Check conditions for a simple transition
      Given a flow definition with a state that has an unguarded transition
      When the developer runs the check command for that state and target
      Then the output indicates no conditions are required

    @id:495c9fd6
    Example: Check conditions for non-existent target reports error
      Given a flow definition with a state
      When the developer runs the check command for a non-existent target
      Then the output indicates the transition target was not found

  Rule: Next Command
    As a developer
    I want to see which transitions pass given a state and evidence
    So that I can determine valid next steps without committing to one

    @id:e0a380b7
    Example: Next with matching evidence shows passing transitions
      Given a flow definition with a state that has a guarded transition
      When the developer runs the next command with matching evidence
      Then the output shows that transition as a valid next step

    @id:79a29725
    Example: Next with non-matching evidence shows no passing transitions
      Given a flow definition with a state that has a guarded transition
      When the developer runs the next command with non-matching evidence
      Then the output shows no passing transitions

    @id:81dc8827
    Example: Next without evidence shows unguarded transitions
      Given a flow definition with a state that has both guarded and unguarded transitions
      When the developer runs the next command without providing evidence
      Then the output shows only the unguarded transitions

    @id:0b719a77
    Example: Next with --json outputs structured results
      Given a flow definition with a state and valid evidence
      When the developer runs the next command with --json
      Then the output is valid JSON containing the passing transitions

  Rule: Transition Command
    As a developer
    I want to compute the next state given a trigger and evidence
    So that I can determine where a transition leads

    @id:0993f68a
    Example: Transition with valid trigger and evidence computes next state
      Given a flow definition with a state that has a guarded transition
      When the developer runs the transition command with a valid trigger and evidence
      Then the output shows the target state

    @id:5302dfcf
    Example: Transition with failing guard condition reports failure
      Given a flow definition with a state that has a guarded transition
      When the developer runs the transition command with failing evidence
      Then the output indicates the transition is not valid

    @id:250c4dce
    Example: Transition to subflow state enters the subflow
      Given a flow definition with a subflow state and the subflow file is available
      When the developer runs the transition command targeting that subflow state
      Then the output shows the first state of the referenced subflow

    @id:dac419ef
    Example: Transition with invalid trigger reports error
      Given a flow definition with a state
      When the developer runs the transition command with an invalid trigger
      Then the output indicates the trigger was not found

    @id:04589cee
    Example: Transition with --json outputs structured result
      Given a flow definition with a state and valid trigger and evidence
      When the developer runs the transition command with --json
      Then the output is valid JSON containing the next state

  Rule: Mermaid Export
    As a developer
    I want to export a flow definition as a Mermaid stateDiagram-v2 diagram
    So that I can visualize the workflow

    @id:1bf637c4
    Example: Mermaid export produces stateDiagram-v2 syntax
      Given a flow definition with states and transitions
      When the developer runs the mermaid command on that file
      Then the output is a valid Mermaid stateDiagram-v2 string

    @id:8c9d008f
    Example: Mermaid export with --json wraps output in JSON
      Given a flow definition
      When the developer runs the mermaid command with --json
      Then the output is valid JSON containing the Mermaid diagram string

  Rule: Image Generation
    As a developer
    I want to generate an image file from a flow definition
    So that I can share workflow diagrams without requiring Mermaid rendering tools

    @deprecated
    @id:3ff0d648
    Example: Image generation creates an image file
      Given a flow definition and the image rendering tool is available
      When the developer runs the image command on that file
      Then an image file is created on disk

    @deprecated
    @id:a3eecc07
    Example: Image generation without rendering tool reports error
      Given a flow definition and the image rendering tool is not installed
      When the developer runs the image command on that file
      Then the output indicates the rendering tool is not available