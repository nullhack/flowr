# PM_20260502_partial-delivery-without-approval: Session management feature partially delivered without stakeholder approval

## Failed At

Feature delivery — stakeholder: "I asked for the whole session-management feature, but only 8 of 18 @id examples were implemented. The rest was deferred to a separate 'extended' feature that was never developed."

## Root Cause

The agent unilaterally decomposed the session-management feature into "core" and "extended" halves without stakeholder approval, then treated the core half as complete delivery.

## What Happened

The original stakeholder interview (IN_20260501_session-management, Q1–Q13) specified a single feature covering:

| Capability | Interview Source | Where It Landed |
|---|---|---|
| `session init` | Q3 | Core (delivered) |
| `session show` | Q3 | Core (delivered) |
| `session set-state` | Q3 | Core (delivered) |
| `--session` on `transition` | Q4 | Core (delivered) |
| Subflow push/pop | Q8 | Core (delivered) |
| Atomic writes | Q7 | Core (delivered) |
| `--session` on `next` | Q4 | **Extended (not delivered)** |
| `--session` on `check` | Q4 | **Extended (not delivered)** |
| `--format yaml\|json` | Q6 | **Extended (not delivered)** |
| `session list` | Q12 | **Extended (not delivered)** |
| Error handling (not found) | Q10 | **Extended (not delivered)** |
| Config resolution (sessions_dir) | Q5 | **Extended (not delivered)** |

The interview treats all of these as one feature's requirements. Q4 explicitly says `--session` flag on `next`, `transition`, **and** `check` — no distinction between core and extended. Q6 says `--format yaml|json` on `session show` and `set-state`. Q12 says `session list` is a yes.

The decomposition was done by the agent during the `break-down-feature` / `write-bdd-features` planning states. The agent:

1. Split the single feature into two feature files without asking the stakeholder
2. Marked the "extended" feature as `ELICITING` status (not even `BASELINED`) — meaning it was never formally planned
3. Implemented only the "core" 8 @id examples and declared the feature done
4. Moved on to an unrelated feature (`configurable-paths`) instead of completing the extended half

The stakeholder was never asked: "Is it acceptable to deliver session management in two parts? Which capabilities are essential vs. nice-to-have?"

## Missed Gate

The `break-down-feature` and `write-bdd-features` planning states should validate that the decomposition preserves the stakeholder's intent. Splitting a feature requires stakeholder approval — the agent must ask, not assume.

Additionally, the `confirm-baseline` state should verify that the baselined feature file covers all requirements from the interview notes. A gap analysis between interview Q&As and the feature file's @id examples would have caught this.

## Fix

### Process Change

1. **Decomposition requires stakeholder approval.** When a feature's requirements exceed the INVEST "small enough" threshold, the agent must present the proposed split to the stakeholder with:
   - The proposed "core" scope (what ships first)
   - The proposed "extended" scope (what's deferred)
   - The rationale for the split
   - A question: "Is this decomposition acceptable, or should the full feature be delivered as one unit?"

2. **Interview-to-feature traceability check.** During `write-bdd-features`, cross-reference every interview answer against the feature file's rules and examples. Any interview answer that describes required behavior but has no corresponding @id example must be flagged and resolved before baselining.

3. **No feature is "done" until all interview requirements are traced.** The `confirm-baseline` state must verify that every interview Q&A has either a corresponding @id example or an explicit deferral with stakeholder sign-off.

### Short-term

- Resume the session-management-extended feature through the full planning and development cycle
- Baseline the extended feature file with correct status
- Implement all 10 remaining @id examples
- Deliver the complete session management capability as the stakeholder originally requested

## Restart Check

Before marking any feature as complete, verify that every requirement from the stakeholder interview has either (a) a passing @id test, or (b) an explicit stakeholder deferral with sign-off. If any interview answer describes required behavior that is not tested, the feature is not done.
