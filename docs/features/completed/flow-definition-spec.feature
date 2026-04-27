Feature: Flow Definition Specification

  The v1 flow definition specification defines the YAML format for describing
  non-deterministic state machine workflows, along with a Python reference
  validator and a Mermaid converter. No existing standard covers the format's
  core features (per-state agent assignment, AI-agent-as-runtime, filesystem-
  as-source-of-truth), so the specification formalizes the existing format with
  clarifications discovered during discovery. The deliverables are: the prose
  specification document, a Python reference validator, a Mermaid converter,
  and reference examples drawn from the project's own flow YAML files.

  Status: BASELINED (2026-04-26)

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-04-22 S1 | Q1–Q7 | Scope pivot: from "Python project template" to "flow specification format" |
  | 2026-04-26 S2 | Q12–Q33 | Created: YAML spec format, validator, Mermaid converter; attrs replace (Q19), fuzzy match (Q20→ADR), numeric extraction (Q21), ambiguous next-target error (Q22), within-flow cycles allowed (Q23), params with defaults (Q24), evidence types deferred (Q25), MUST/SHOULD conformance (Q26), no JSON Schema (Q27), reference validator (Q28), no transition counts (Q29), existing flows as examples (Q30), immutable flows MUST / filesystem SHOULD (Q32), format-agnostic naming (Q33) |

  Rules (Business):
  - State-level attrs replace flow-level attrs entirely (no merge, no deep merge)
  - The ~= operator is a numeric approximate match: passes if the evidence value is within 5% of the condition value
  - Numeric extraction strips non-numeric suffixes from both condition and evidence values before comparison
  - A next target that matches both a state id and an exit name is a validation error (ambiguous reference)
  - Within-flow cycles are allowed; cross-flow cycles are forbidden
  - Params are declarations with optional default values; missing params without defaults are validation errors
  - Conformance levels are MUST (required) and SHOULD (recommended)
  - Immutable loaded flows are a MUST requirement; filesystem truth is a SHOULD guideline
  - The specification format has its own format-agnostic name; flowr is one implementation

  Constraints:
  - No runtime engine in v1 — only the flow definition format
  - No session tracking in v1 — a simple session file holds current flow, state, and stack only (no transition history, no versioning)
  - No JSON Schema deliverable — internal representation uses Python dataclasses; JSON is only for CLI communication
- Evidence type system: all evidence values are coerced to strings before comparison; YAML booleans become lowercase, YAML numbers become numeric strings (ADR-2026-04-26-evidence-type-system)
- Fuzzy match algorithm: the ~= operator applies ONLY to numeric values with 5% tolerance; string matching is not supported (ADR-2026-04-26-fuzzy-match-algorithm)

  Rule: Flow Definition
    As a developer
    I want to define a workflow in YAML with required top-level fields
    So that my process is machine-readable and verifiable

    @id:ccf4a4ba
    Example: Minimal valid flow
      Given a YAML document with flow, version, exits, and one state
      When the validator loads the flow definition
      Then the flow definition passes validation

    @id:68055fed
    Example: Missing required field is rejected
      Given a YAML document without the exits field
      When the validator loads the flow definition
      Then the validator reports a MUST-level error identifying the missing field

    @id:8360294d
    Example: Flow with attrs and no states is rejected
      Given a YAML document with flow, version, exits, and attrs but no states
      When the validator loads the flow definition
      Then the validator reports a MUST-level error identifying the missing states field

    @id:cbf72d71
    Example: First state is the initial state
      Given a YAML document with multiple states in order
      When the validator loads the flow definition
      Then the first state in the list is identified as the initial state

  Rule: State Transitions
    As a developer
    I want to define states with simple and guarded transitions
    So that I can model non-deterministic workflows

    @id:730066c8
    Example: Simple transition with string target
      Given a state with next mapping go: done where done is an exit name
      When the validator resolves the transition
      Then the transition target resolves to the exit named done

    @id:01b2e389
    Example: Guarded transition with when conditions
      Given a state with next mapping approve: { to: approved, when: { score: ">=80%" } }
      When the validator loads the flow definition
      Then the guarded transition is recognized with condition score >=80%

    @id:eb8f6172
    Example: Mixed simple and guarded transitions in one state
      Given a state with next containing both simple and guarded transitions
      When the validator loads the flow definition
      Then both transition types are recognized in the same state

    @id:78fa1402
    Example: Plain string condition treated as equality
      Given a when condition with value pass (no operator prefix)
      When the validator parses the condition
      Then the condition is treated as ==pass

  Rule: Subflow Invocation
    As a developer
    I want to invoke subflows from a state
    So that I can compose complex workflows from simpler ones

    @id:bf07819e
    Example: State invokes subflow by name
      Given a state with flow: scope-cycle and flow-version: "^1"
      When the validator loads the flow definition
      Then the state is recognized as a subflow invocation

    @id:db51954e
    Example: Parent next keys match child exits
      Given a parent state invoking scope-cycle with next keys complete and blocked matching the child exits
      When the validator checks the subflow contract
      Then the subflow invocation passes validation

    @id:e19a1a33
    Example: Parent next keys mismatch child exits
      Given a parent state invoking scope-cycle with next key success that is not in the child exits
      When the validator checks the subflow contract
      Then the validator reports a MUST-level error for the mismatched exit

  Rule: Attr Override
    As a developer
    I want state-level attrs to replace flow-level attrs entirely
    So that per-state overrides have no merge ambiguity

    @id:a50ab6c3
    Example: State attrs replace flow attrs entirely
      Given a flow with attrs { timeout: 300, retry: 2 } and a state with attrs { timeout: 600, docker: true }
      When the validator resolves the state attrs
      Then the effective attrs for that state are { timeout: 600, docker: true } with no retry key

    @id:13e298f1
    Example: State without attrs inherits nothing from flow attrs
      Given a flow with attrs { owner: platform-team } and a state without attrs
      When the validator resolves the state attrs
      Then the state has no attrs (flow-level attrs are not inherited to states without attrs)

  Rule: Condition Operators
    As a developer
    I want condition operators in guard conditions
    So that I can express transition constraints with equality, inequality, numeric comparison, and approximate numeric matching

    @id:2ce2f6b6
    Example: Equality operator matches exact string
      Given a when condition all_tests_pass: "==true" and evidence all_tests_pass: "true"
      When the condition is evaluated
      Then the condition is satisfied

    @id:34300527
    Example: Inequality operator rejects matching string
      Given a when condition verdict: "!=pass" and evidence verdict: "fail"
      When the condition is evaluated
      Then the condition is satisfied

    @id:5fb078c6
    Example: Greater-than-or-equal operator with numeric extraction
      Given a when condition score: ">=80%" and evidence score: "92%"
      When the condition is evaluated
      Then numeric extraction compares 92 >= 80 and the condition is satisfied

    @id:c43b1128
    Example: Less-than operator with plain number
      Given a when condition errors: "<3" and evidence errors: "1"
      When the condition is evaluated
      Then the condition compares 1 < 3 and is satisfied

    @id:bdd51f94
    @deprecated
    @id:8173b81d
    Example: Fuzzy match operator matches case-insensitive substring
      Given a when condition verdict: "~=pass" and evidence verdict: "passing_grade"
      When the condition is evaluated
      Then the condition is satisfied because pass is a case-insensitive substring of passing_grade

    @id:7711a3c7
    @deprecated
    @id:5e31b949
    Example: Fuzzy match operator rejects non-matching string
      Given a when condition verdict: "~=pass" and evidence verdict: "fail"
      When the condition is evaluated
      Then the condition is not satisfied

    @id:980735f8
    Example: Approximate match operator passes for values within 5 percent
      Given a when condition score: "~=100" and evidence score: "97"
      When the condition is evaluated
      Then the condition is satisfied because 97 is within 5 percent of 100

    @id:c91e0aaa
    Example: Approximate match operator fails for values outside 5 percent
      Given a when condition score: "~=100" and evidence score: "90"
      When the condition is evaluated
      Then the condition is not satisfied because 90 is more than 5 percent away from 100

    @id:7ea0ad82
    Example: Numeric extraction strips both condition and evidence
      Given a when condition score: ">=80%" and evidence score: "75%"
      When the condition is evaluated
      Then numeric extraction strips the percent from both values and compares 75 >= 80 as false

  Rule: Transition Resolution
    As a developer
    I want every next target to resolve unambiguously
    So that the validator rejects flows with ambiguous references

    @id:77b26097
    Example: Next target resolves to a state
      Given a next target step-2 that matches a state id but not an exit name
      When the validator resolves the target
      Then the target resolves to the state with id step-2

    @id:696085fd
    Example: Next target resolves to an exit
      Given a next target done that matches an exit name but not a state id
      When the validator resolves the target
      Then the target resolves to the exit named done

    @id:e60b9e41
    Example: Next target matching both state and exit is ambiguous
      Given a next target complete that matches both a state id and an exit name
      When the validator resolves the target
      Then the validator reports a MUST-level error for the ambiguous reference

    @id:f55badc3
    Example: Next target matching neither state nor exit is invalid
      Given a next target nonexistent that matches neither a state id nor an exit name
      When the validator resolves the target
      Then the validator reports a MUST-level error for the unresolvable target

  Rule: Cycle Validation
    As a developer
    I want within-flow cycles allowed and cross-flow cycles rejected
    So that I can model iterative processes without infinite recursion

    @id:7fe4a980
    Example: Within-flow cycle is valid
      Given a flow where state discovery has a transition more-discovery targeting discovery itself
      When the validator checks for cycles
      Then the flow passes validation because within-flow cycles are allowed

    @id:c4a19ac3
    Example: Cross-flow cycle is rejected
      Given flow A invokes flow B as a subflow and flow B invokes flow A as a subflow
      When the validator checks for cycles
      Then the validator reports a MUST-level error for the cross-flow cycle

  Rule: Param Defaults
    As a developer
    I want flow parameters with optional defaults
    So that my flows can accept configuration at invocation time

    @id:a916050b
    Example: Required param missing at invocation is an error
      Given a flow declaring params: [feature_slug] without a default value
      When the flow is invoked without providing feature_slug
      Then the validator reports a MUST-level error for the missing required param

    @id:a62cea4d
    Example: Optional param with default value is satisfied
      Given a flow declaring params with name: verbose and default: false
      When the flow is invoked without providing verbose
      Then the param verbose takes the default value false

    @id:9e711cf8
    Example: Provided param overrides default
      Given a flow declaring params with name: verbose and default: false
      When the flow is invoked with verbose: true
      Then the param verbose takes the provided value true

  Rule: Exit Contract
    As a developer
    I want exits to be always required and parent next keys to match child exits
    So that subflow contracts are explicit and verifiable

    @id:2286f192
    Example: Flow without exits is rejected
      Given a YAML document without the exits field
      When the validator loads the flow definition
      Then the validator reports a MUST-level error for the missing exits

    @id:c513f294
    Example: Parent next keys exactly match child exits
      Given a parent state invoking a subflow with exits [complete, blocked]
      When the parent state defines next keys [complete, blocked]
      Then the subflow contract passes validation

    @id:c5bb3397
    Example: Exit with no referencing state is flagged
      Given a flow with exits [done] where no state references done in any next mapping
      When the validator checks exit references
      Then the validator reports a SHOULD-level warning for the unreferenced exit

  Rule: Session Format
    As a developer
    I want a minimal session format that tracks the current flow, state, and call stack
    So that I can persist and resume workflow progress

    @id:33ace791
    Example: Session format tracks current flow and state
      Given a session file with current flow: scope-cycle and current state: discovery
      When the session is loaded
      Then the current position in the workflow is identified as scope-cycle/discovery

    @id:4354f16e
    Example: Session stack tracks subflow nesting
      Given a session file with a stack containing the parent flow and state
      When the session is loaded
      Then the call stack correctly represents the subflow nesting depth

    @id:7496768d
    Example: Session format has no transition history
      Given a valid session file
      When the session format is validated
      Then no transition count or history fields are present

  Rule: Mermaid Conversion
    As a developer
    I want to generate Mermaid diagrams from flow definitions
    So that I can visualize my workflows

    @id:9540cdc3
    Example: Simple flow generates valid Mermaid diagram
      Given a valid flow definition with states and transitions
      When the Mermaid converter processes the flow
      Then the output is a valid Mermaid stateDiagram-v2 diagram representing all states and transitions

    @id:82915538
    Example: Subflow invocation is represented in Mermaid output
      Given a flow definition containing a subflow invocation
      When the Mermaid converter processes the flow
      Then the subflow state is represented with a reference to the invoked flow name

  Rule: Conformance
    As a tool author
    I want clear MUST/SHOULD conformance levels
    So that my validator reports the right severity for each rule

    @id:1aa411c3
    Example: Immutable flows is a MUST requirement
      Given a conforming implementation that loads flow definitions
      When a loaded flow definition is modified after loading
      Then the implementation rejects the modification as a MUST-level violation

    @id:cd40fd6e
    Example: Filesystem truth is a SHOULD guideline
      Given a conforming implementation that detects a conflict between the filesystem and session cache
      When the implementation resolves the conflict
      Then the filesystem version takes precedence as a SHOULD-level recommendation

    @id:23b797eb
    Example: Validator distinguishes MUST and SHOULD rule severity
      Given a conforming validator processing a flow definition
      When the validator reports violations
      Then each violation is classified as either MUST (required) or SHOULD (recommended)