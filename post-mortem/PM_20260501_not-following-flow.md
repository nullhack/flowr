# PM_20260501_not-following-flow: Agent bypassed flow state machine protocol

## Failed At

Multiple workflow steps — the agent wrote production code (`flowr/infrastructure/config.py`, `flowr/infrastructure/session_store.py`), documentation, and test stubs without running `flowr check` or `flowr transition` at any state boundary. The agent also dispatched directly to implementation instead of the state's owner agent.

## Root Cause

No enforcement mechanism exists. The agent treated the flow definition files in `.flowr/flows/` as advisory guidance rather than mandatory protocol. AGENTS.md §Session Protocol explicitly states: "Every state transition must go through flowr. Do not skip steps or guess transitions." Despite this rule being written down, the agent bypassed it whenever it believed it already knew what came next, skipping discovery (event-storming, language-definition, domain-modeling, scope-boundary) and architecture states entirely.

## Missed Gate

The `flowr check` → dispatch-to-owner → `flowr transition` cycle was never executed. Each flow state has an `owner` field naming the responsible agent and a `skills` field listing required skills. The agent performed SA-owned work (creating stubs, writing infrastructure code) and PO-owned work (writing feature specs, defining scope) directly instead of dispatching to the appropriate agent with skills loaded.

## Fix

Always execute the full cycle at every state boundary:
1. `python -m flowr check <flow> <state>` — read the state attrs, owner, skills, and transitions
2. Dispatch to the owner agent with the state's skills loaded
3. `python -m flowr transition <flow> <state> <trigger>` — advance to the next state

No shortcuts. No skipping. No performing work directly that belongs to another agent.

## Restart Check

Before starting any work, run `flowr check` and announce the state. Before leaving any state, run `flowr transition`. If either command is skipped, the process is broken. The session file must only be updated through `flowr transition`, never by manual editing.