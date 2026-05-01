# Post-Mortem: Agent Role Violation During TDD Cycle

> **Date:** 2026-05-02
> **Severity:** Process
> **Status:** Open

## What Happened

During the TDD cycle for `cli-flow-name-resolution`, the orchestrator agent violated three process rules simultaneously:

1. **Did not dispatch to the SE agent.** The `tdd-cycle` state is owned by the Software Engineer (SE). Instead of dispatching to the SE agent with the `implement-minimum` skill loaded, the orchestrator wrote implementation code and test bodies directly.

2. **Performed reviewer work during TDD.** After writing implementation code, the orchestrator ran `ruff check` and began fixing lint errors, convention violations, and formatting issues. Convention enforcement is the **reviewer's** responsibility at the `review-gate` state — not the SE's during `tdd-cycle`.

3. **Wore multiple hats.** The orchestrator acted as SE (writing code), reviewer (running lint), and orchestrator (deciding what to do next) in the same turn, with no agent boundaries between these roles.

## Root Cause

The orchestrator treated the TDD cycle as a "get everything working and clean" phase rather than a strict RED-GREEN-REFACTOR cycle owned by a specific agent. This conflated three distinct responsibilities:

- **SE:** Write minimum code to make failing tests pass (RED → GREEN), then improve structure while keeping tests green (REFACTOR)
- **Reviewer:** Verify conventions, lint, type-checking, and design alignment at the review gate
- **Orchestrator:** Dispatch to the correct agent, pass the right skills, and transition the flow

The orchestrator skipped the dispatch step and collapsed all three roles into one, resulting in:
- Convention changes mixed into implementation commits
- No independent review — the same entity that wrote the code also "reviewed" it
- Loss of the quality gate that the review state provides

## Missed Gate

The **agent dispatch protocol** was violated. Every flow state has an `owner` field that names the responsible agent. The orchestrator must dispatch to that agent with the listed skills loaded — never perform the work directly.

Additionally, the **TDD minimum rule** was violated: the SE writes only the minimum production code needed to make the failing test pass. Convention fixes (exception renaming, line length, docstrings, import cleanup) are not minimum — they are review concerns.

## Fix

1. **Always dispatch to the state's owner agent.** The orchestrator never writes implementation code. It dispatches, collects results, and transitions.

2. **Minimum TDD as a golden rule.** The SE writes the smallest possible change to make the test pass. No convention fixes, no formatting, no lint satisfaction during TDD. Those belong to the reviewer.

3. **Convention changes are review-gate concerns.** Lint, format, type-checking, and docstring enforcement happen at `review-gate`, not during `tdd-cycle`. The SE's refactoring step is about code structure (removing duplication, improving naming that affects behavior), not about satisfying linters.

## Golden Rule

**Minimum TDD: write the smallest change that makes the test pass. Convention enforcement is the reviewer's job.**

## Restart Check

- The functional implementation (flow name resolution in `resolution.py`, `__main__.py` wiring, test bodies) is correct and all 7 tests pass
- The convention changes (exception renaming, line wrapping, trailing newlines, unused import removal) need to be reverted from the feature branch — they should be introduced at the review gate, not during TDD
- Existing test suite (172 passed, 12 skipped) remains green
