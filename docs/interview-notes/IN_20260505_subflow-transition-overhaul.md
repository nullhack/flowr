# IN_20260505_subflow-transition-overhaul — Subflow mechanism and agent UX overhaul

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## Feature: subflow-transition-overhaul

| ID | Question | Answer |
|----|----------|--------|
| Q1 | What is the core problem discovered? | A full dry run of the main-flow revealed two critical bugs that make the entire subflow mechanism non-functional for real flows, plus multiple agent UX gaps that would prevent effective navigation even after the bugs are fixed. |
| Q2 | What is the first critical bug? | `resolve_subflows()` in `loader.py:39` constructs paths as `root_path.parent / state.flow`, but real flow references omit the `.yaml` extension (e.g., `flow: discovery-flow`). The resulting path `.flowr/flows/discovery-flow` doesn't exist, so subflows are never resolved. Tests pass because fixtures use explicit `.yaml` extensions. |
| Q3 | What is the second critical bug? | When a subflow exits, `pop_stack(target)` at `__main__.py:596` uses the exit name directly as the new state (e.g., `"complete"`), but it should resolve through the parent flow's transition map. In `main-flow`, `discovery` state maps `complete → architecture`, but the session ends up at the invalid state `main-flow/complete`. The agent is dead-ended. |
| Q4 | Does `session init` handle initial subflows? | No. When the first state has a `flow:` field (like `main-flow/discovery` which has `flow: discovery-flow`), `session init` sets the state but never pushes the subflow stack. The agent sits at the wrapper state without entering the subflow. |
| Q5 | What is the `next` command's output problem? | `next` shows only TARGET state names (e.g., `next: event-storming`), but agents need TRIGGER names to transition (e.g., `needs_full_discovery`). There is no combined view showing the trigger→target mapping. The agent must run both `check` (for trigger names) and `next` (for target states) and mentally map them. |
| Q6 | What about guarded transitions? | `next` filters out transitions whose conditions aren't met by the provided evidence. An agent that hasn't provided evidence sees fewer transitions — potentially zero — with no indication that guarded transitions exist or what evidence they need. This is especially dangerous at exit transitions like `scope-boundary`'s `done → complete` which requires `committed_to_main_locally=verified`. |
| Q7 | Does `check --session <target>` work? | No. The argparse captures the target argument as the `flow_file` positional (because `flow_file` is the first optional positional). So `check --session project approved` sets `flow_file="approved"` and `target=None`, showing state details instead of transition conditions. |
| Q8 | Can `set-state` cross flow boundaries for recovery? | No. `set-state` validates the target state exists in the current flow only. Subflow states aren't in the parent flow's state list, so you can't teleport into a subflow. And the stack isn't managed either. |
| Q9 | What about `--session` on other commands? | `--session` only exists on `check`, `next`, and `transition`. You can't run `states --session` to list states in your current (sub)flow, or `validate --session` to validate it. |
| Q10 | What design decisions were made? | (1) `next` should ALWAYS show all transitions including guarded/blocked ones, with status markers — agents need the full picture. (2) JSON output for `next` should be a clean break: replace `"next": [strings]` with `"transitions": [{trigger, target, status, conditions}]`. No backward compatibility needed. |
| Q11 | What is the proposed subflow exit fix? | When a subflow exit is detected: (1) load the parent flow from the stack frame, (2) look up the exit trigger in the parent state's `next` map, (3) use the resolved target as the new state, (4) check if the resolved target enters ANOTHER subflow (handle chaining). This requires passing `flows_dir` to `_apply_session_transition`. |
| Q12 | Should the `next` text output format change? | Yes. From `next: event-storming` to `  needs_full_discovery → event-storming` with inline condition hints: `  done → complete (needs: committed_to_main_locally=verified)` or `  done → complete (blocked: committed_to_main_locally=verified)`. |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA1 | Reliability | When a session transitions through a subflow exit, the parent transition is correctly resolved and the session lands on a valid state in the parent flow | Subflow exit always resolves through parent transition map | Must |
| QA2 | Reliability | When a flow references a subflow by name without `.yaml`, the subflow is resolved correctly | Try path as-is, then with `.yaml` appended | Must |
| QA3 | Usability | When an agent runs `next`, all available transitions are visible including guarded ones that need evidence | Always show all transitions with status markers | Must |
| QA4 | Usability | When an agent runs `next`, trigger names are visible alongside target states | Show `trigger → target` format | Must |
| QA5 | Discoverability | When an agent runs `next`, evidence keys required by guarded transitions are visible inline | Show condition key=value requirements in output | Must |
| QA6 | Backward Compatibility | Non-session commands continue to work identically | Zero behavior change for non-session invocations | Must |

---

## Pain Points Identified

- Subflow mechanism is completely non-functional for real flows — two critical bugs prevent any subflow from being entered or exited correctly
- `next` command hides critical information: trigger names, guarded transitions, and evidence requirements are all invisible
- Session can enter an invalid state (non-existent state ID) from which recovery requires manual YAML editing
- `session init` leaves the agent stranded at a wrapper state instead of entering the initial subflow
- No single command gives the agent a complete picture of where they are and what they can do
- `check --session <target>` silently ignores the target argument due to argparse capture
- Evidence keys are completely undiscoverable — the agent must read raw YAML to know what to provide
- Tests have a false-positive gap: fixtures use `.yaml` extensions in flow references, hiding the resolve_subflows bug

## Business Goals Identified

- Make the subflow mechanism actually work for real multi-level flow hierarchies
- Enable agents to navigate flows autonomously by making all navigation information visible from CLI commands
- Prevent sessions from entering invalid/broken states
- Support subflow→subflow chaining (e.g., main-flow → discovery-flow → exit → architecture-flow)

## Terms to Define (for glossary)

- Subflow entry — the push-stack operation when transitioning to a state with a `flow:` field
- Subflow exit — the pop-stack operation when a transition targets a name in the flow's `exits` list
- Exit resolution — resolving the exit name through the parent flow's transition map to get the actual target state
- Subflow chaining — entering a new subflow immediately after exiting one (e.g., discovery-flow exits → main-flow transitions → architecture-flow enters)
- Blocked transition — a guarded transition whose conditions are not met by the provided evidence

## Action Items

- [ ] Fix `resolve_subflows()` to handle missing `.yaml` extension
- [ ] Fix subflow exit to resolve parent transition target with chaining support
- [ ] Fix `session init` to auto-enter initial subflow
- [ ] Enhance `next` output to show trigger→target mapping with conditions
- [ ] Fix `check --session <target>` argparse dispatch
- [ ] Add `--session` to `states` and `validate`
- [ ] Add tests without `.yaml` extension in flow references
- [ ] Add tests for subflow exit resolution and chaining
