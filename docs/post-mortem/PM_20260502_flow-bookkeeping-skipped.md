# PM_20260502_flow-bookkeeping-skipped: Agent completed features but skipped flow transitions, file moves, and acceptance gates

## Failed At

After successfully implementing and merging both `cli-flow-name-resolution` and `session-management-core` to local main, the agent failed to:

1. Transition the development flow from `commit` → `done` for session-management-core
2. Transition the main flow from `feature-development` → `completed` for session-management-core
3. Move feature files from `backlog/` to `completed/` for either feature
4. Run the acceptance gate (accept-feature) for either feature

The session YAML was manually set to `development-flow / project-structuring` for `session-management-core` instead of being driven by `flowr transition`. The cli-flow-name-resolution feature's main-flow transitions were done correctly (completed), but its feature file was never moved out of backlog.

## Root Cause

The agent treated the development work (TDD, review, commit, merge) as the finish line. Once code was committed and merged, the agent declared the features "done" without completing the flow state machine's remaining states. This is the same class of error as PM_20260501_session-not-updated — treating the session file as editable configuration rather than flow-engine-owned state — but extended to the entire post-implementation lifecycle.

The agent manually wrote the session YAML file for session-management-core (`flow: development-flow, state: project-structuring`) instead of using `flowr check` → `flowr transition` to drive state changes. When the implementation was complete, the agent did not transition through commit → done → feature-development completed → acceptance → delivery.

Additionally, feature files are supposed to move from `backlog/` to `in-progress/` when development starts, and from `in-progress/` to `completed/` when accepted. The agent never moved any feature files.

## Missed Gate

The flow state machine exists precisely to prevent this class of error. Each state defines what must happen before moving on. By skipping states:

- **commit** state was skipped — the agent committed directly without going through the flow
- **accept-feature** was skipped — no PO acceptance happened
- **delivery** was skipped — no formal delivery step
- Feature file locations are stale — they still show `backlog/` for completed features
- The session file is stale — it shows a state that doesn't reflect reality

## Fix

After implementation is complete, the agent MUST:

1. Use `flowr transition` for every state change — never manually edit the session YAML
2. Transition the development flow through: tdd-cycle (all_green) → review-gate (pass) → commit → done
3. Pop the stack back to the main-flow and transition: feature-development → acceptance
4. Run the acceptance skill to validate against BDD scenarios
5. Transition acceptance → delivery → complete
6. Move the feature file from `backlog/` → `in-progress/` (at development start) → `completed/` (at acceptance)

## Golden Rule

**Implementation is not completion.** Merging code to main is one step in a multi-state lifecycle. The flow state machine tracks the full lifecycle — skipping states means skipping quality gates.

## Restart Check

After any commit, verify:
- The session YAML reflects the correct flow and state (via `flowr check`)
- Feature files are in the correct directory (backlog → in-progress → completed)
- All flow transitions were driven by `flowr transition`, not manual edits