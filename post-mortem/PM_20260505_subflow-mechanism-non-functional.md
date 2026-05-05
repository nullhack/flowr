# PM_20260505_subflow-mechanism-non-functional: Two critical bugs made the entire subflow mechanism non-functional for real flows

## Failed At

Production readiness — a full dry run of the main-flow discovered that the subflow mechanism (push/pop stack for nested flows) was completely broken. Subflows could not be entered (path resolution bug) and could not be exited correctly (exit resolution bug). The session-management features were delivered and tested, but the tests had a false-positive gap: fixtures used `.yaml` extensions in flow references, hiding the path resolution bug.

## Root Cause

Two independent bugs in the CLI/transition layer, plus a systematic testing gap:

1. **Path resolution bug** (`loader.py:39`): `resolve_subflows()` constructs paths as `root_path.parent / state.flow`, but real flow definitions omit the `.yaml` extension (e.g., `flow: discovery-flow`). The resulting path doesn't exist, so subflows are never loaded into the resolved flow graph. Tests pass because all test fixtures use explicit `.yaml` extensions (e.g., `flow: child.yaml`).

2. **Exit resolution bug** (`__main__.py:596`): When a subflow exits via `pop_stack(target)`, the exit name (e.g., `"complete"`) was used directly as the new state. But the parent flow's transition map maps exit names to real target states (e.g., `complete → architecture`). The session ended up at the invalid state `main-flow/complete` — a state that doesn't exist in main-flow. The agent is dead-ended.

3. **Stack frame bug** (`__main__.py:654`): `_enter_subflow()` recorded `session.state` (the pre-transition state) instead of `target_state_id` (the subflow wrapper state) in the stack frame. On subflow exit, `_resolve_subflow_exit()` looks up the exit name in the parent state's `next` map — but the stack pointed to the wrong state, so the lookup failed silently and fell back to using the exit name as a bare state ID. Example: entering tdd-cycle from `development-flow/project-structuring` pushed `{state: project-structuring}`, but the exit map lives on the `tdd-cycle` state — so `blocked` couldn't resolve to `project-structuring`.

4. **Testing gap**: Tests used `.yaml` extensions in flow references and tested subflow exit only to exit names that happened to also be valid state IDs in the parent flow. No test exercised the full production flow hierarchy or verified that the stack frame pointed to the correct parent state.

## What Happened

The session-management feature was implemented in two phases (core + extended) and all tests passed. However, when the main-flow was dry-run end-to-end for the first time, every subflow transition failed:

| Step | Expected | Actual | Bug |
|------|----------|--------|-----|
| `session init main-flow` | Enter `discovery-flow/stakeholder-interview` | Stay at `main-flow/discovery` | `resolve_subflows` fails, `session init` doesn't enter subflow |
| Transition inside discovery-flow | Move to next state | Success (no subflow needed) | — |
| Exit discovery-flow → enter architecture-flow | `main-flow/architecture` → enter `architecture-flow/architecture-assessment` | Session at invalid state `main-flow/complete` | Exit uses exit name directly, not parent transition target |

Additionally, even if the subflow mechanism had worked, the agent UX would have been broken:

- `next` showed only target state names without trigger names — agents couldn't discover which trigger to use
- `next` hid guarded/blocked transitions — agents saw fewer options than actually available
- `check --session <target>` silently swallowed the target argument due to argparse capturing it as `flow_file`
- `states --session` and `validate --session` didn't exist

## Missed Gate

**Test fixtures should match production conventions.** The test fixtures used `flow: child.yaml` (with extension) while real flows use `flow: discovery-flow` (without extension). No validation ensured that test fixtures represented realistic flow definitions.

**E2E smoke test.** No test exercised the complete flow hierarchy (main-flow → discovery-flow → exit → architecture-flow). The feature was declared complete based on unit tests with simplified fixtures that didn't reproduce the production bug surface.

## Fix

### Phase 1: Critical Bugs (sf-001 through sf-007)

| ID | Fix | File | Change |
|----|-----|------|--------|
| sf-001, sf-002 | `resolve_subflows()` tries path as-is, then appends `.yaml` | `flowr/domain/loader.py:34-48` | Added fallback: `if not subflow_path.exists(): subflow_path = parent / (state.flow + ".yaml")` |
| sf-003 | Subflow exit resolves through parent's transition map | `flowr/__main__.py:660-694` | New `_resolve_subflow_exit()`: loads parent flow from stack, looks up exit name in parent state's `next` map, uses resolved target |
| sf-004 | Subflow chaining: exit + immediate entry into next subflow | `flowr/__main__.py:688-694` | `_resolve_subflow_exit()` calls `_enter_subflow()` on the resolved target, handling chains like discovery → architecture |
| sf-005 | Invalid parent state produces clear error | `flowr/__main__.py:679-680` | Fallback to `pop_stack(exit_name)` when parent flow/state can't be resolved |
| sf-006, sf-007 | `session init` auto-enters initial subflow | `flowr/cli/session_cmd.py:97-108` | After `store.init()`, checks if first state has `flow:` field, resolves subflow, pushes stack |
| sf-bug | Stack frame records subflow wrapper state (not pre-transition state) | `flowr/__main__.py:654` | Changed `state=session.state` to `state=target_state_id` — exit resolution now finds the correct parent `next` map |

### Phase 2: Agent UX (sf-008 through sf-014)

| ID | Fix | File | Change |
|----|-----|------|--------|
| sf-008-sf-011 | `next` shows all transitions with trigger→target, status, conditions | `flowr/__main__.py:516-557` | New `_build_transition_list()` and `_format_transitions_text()`; JSON replaces `next: [strings]` with `transitions: [{trigger, target, status, conditions}]` |
| sf-012 | `check --session <target>` correctly routes target argument | `flowr/__main__.py:807-825` | Uses `effective_target = args.target or getattr(args, "flow_file", None)` when `--session` is active |
| sf-013, sf-014 | `states --session` and `validate --session` resolve current flow | `flowr/__main__.py:933+` | New `_cmd_states_session()` and `_cmd_validate_session()`; dispatch refactored into `_dispatch_session_command()` |

### Testing

- Added tests for `resolve_subflows` without `.yaml` extension
- Added `TestSubflowExitResolution` with 4 tests: simple exit, chaining, fallback, push without extension
- Updated `next_command_test.py` to match new output format
- All existing tests pass (no regressions)

### Key Design Decisions

1. **`next` ALWAYS shows all transitions** — including blocked/guarded ones with status markers. Agents need the full picture even when they can't take a transition yet.
2. **JSON output is a breaking change** — `next` array of strings replaced with `transitions` array of objects. No backward compatibility needed (pre-release).
3. **Subflow exit uses exit name as parent trigger** — the exit name (e.g., `complete`) is looked up in the parent state's `next` map to find the real target.
4. **Chaining is handled inline** — `_resolve_subflow_exit` calls `_enter_subflow` on the resolved target, so discovery→architecture chaining is atomic.

## Restart Check

Before declaring any feature "complete and tested":

1. **Dry run the production flow end-to-end.** Unit tests with simplified fixtures are necessary but not sufficient. Run `session init` → full flow → completion against the actual flow hierarchy before closing the feature.
2. **Test fixtures must match production conventions.** If production flows omit `.yaml` extensions, test fixtures must omit them too. Audit fixture conventions against real flow definitions.
3. **Test the full transition chain, not individual links.** Subflow entry, execution, and exit must be tested as a complete sequence, not as isolated unit tests that happen to pass individually.
4. **Verify agent UX, not just correctness.** After fixing bugs, verify that an agent using only CLI commands can discover triggers, conditions, and navigate the full flow without reading raw YAML files.
