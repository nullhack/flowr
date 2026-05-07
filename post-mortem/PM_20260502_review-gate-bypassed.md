# PM_20260502_review-gate-bypassed.md

## Failed At
Review-gate for cli-flow-name-resolution. The orchestrator dispatched a reviewer task that evaluated all three review tiers (design, structure, conventions) in a single pass, instead of following the review-gate-flow which defines three separate sequential states: `design-review` → `structure-review` → `conventions-review`.

## Root Cause
The orchestrator treated the review-gate as a single monolithic review step, dispatching one reviewer task that covered all three tiers at once. This bypassed the progressive gate design where each tier is an independent state with its own `pass`/`fail` transitions.

The review-gate-flow explicitly defines:
- `design-review` — pass → `structure-review`, fail → exit `fail`
- `structure-review` — pass → `conventions-review`, fail → exit `fail`
- `conventions-review` — pass → exit `pass`, fail → exit `fail`

Each state should be entered via `flowr transition`, evaluated independently, and only if it passes should the next state be entered. If any tier fails, the feature goes back to the TDD cycle — not to the next review tier.

The orchestrator's task description asked the reviewer to "report a structured review with three sections" covering design, structure, and conventions simultaneously. This defeats the purpose of the progressive gate: a design failure should block structure review entirely, and a structure failure should block conventions review.

## Missed Gate
The **progressive review gate** — each review tier is a separate flow state that must be entered, evaluated, and transitioned individually. The orchestrator collapsed three states into one task invocation.

## Fix
1. Enter `design-review` via `flowr transition`, dispatch reviewer with `review-design` skill only
2. If design-review passes, transition to `structure-review`, dispatch reviewer with `review-structure` + `verify-traceability` skills
3. If structure-review passes, transition to `conventions-review`, dispatch reviewer with `review-conventions` skill
4. If any tier fails, transition to `fail` and return to TDD cycle

The orchestrator must never combine multiple flow states into a single task invocation. Each state in a flow is a separate checkpoint with its own owner, skills, and transition logic.

## Golden Rule
**Each flow state is a separate gate. Enter them one at a time via `flowr transition`, dispatch only that state's owner with only that state's skills. Never collapse multiple review states into one task.**

## Restart Check
- The implementation code is unchanged and correct
- The review-gate-flow is correctly defined in `.flowr/flows/review-gate-flow.yaml`
- The orchestrator needs to re-enter `design-review` properly and proceed one state at a time