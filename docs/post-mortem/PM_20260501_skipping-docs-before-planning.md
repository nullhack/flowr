# PM_20260501_skipping-docs-before-planning: Agent jumped to planning states without required input artifacts

## Failed At

Planning flow — the agent attempted to enter feature-selection and feature-specification states for the `cli-flow-name-resolution` and `session-management` features without the required `in` artifacts existing on disk. The planning-flow states require `product_definition.md`, `technical_design.md`, `domain_model.md`, and `glossary.md` as inputs. These files were lost (wiped by `git clean` during a branch operation) and never reconstructed.

## Root Cause

The agent treated file loss as a signal to "move forward anyway" rather than a signal to "reconstruct prerequisites first." The discovery-flow produces these documents through its states (interview notes → event storming → language definition → domain modeling → scope boundary → product definition). The agent skipped the entire discovery flow, jumped to planning, and started writing feature specs and code without ensuring the required inputs existed. Additionally, the agent created `flowr/infrastructure/config.py` and `flowr/infrastructure/session_store.py` as production code — work that should only happen during the TDD cycle in the development flow, not during discovery or planning.

## Missed Gate

Each flow state's `in` list defines what must exist before that state can do its work. The `feature-selection` state requires `product_definition.md` and `technical_design.md`. The `feature-specification` state requires `product_definition.md`, `domain_model.md`, `glossary.md`, and `technical_design.md`. If an `in` artifact doesn't exist, the agent must run the upstream flow state that produces it — or raise an error for the stakeholder. The agent never checked whether these files existed.

## Fix

Before entering any state, verify all `in` artifacts exist on disk. If they don't:
1. Run the upstream flow states that produce them
2. If the upstream state doesn't apply (e.g., the domain model already exists but the file was lost), reconstruct from the last known good state
3. Never skip to a downstream state whose inputs are missing

For this project: `docs/spec/product_definition.md`, `docs/spec/glossary.md`, `docs/spec/domain_model.md`, `docs/spec/technical_design.md`, `docs/spec/system.md`, and `docs/spec/context_map.md` must all exist before entering the planning flow. They were previously written but lost; they need reconstruction through the proper flow.

## Restart Check

List the `in` artifacts for the target state. Verify each file exists. If any are missing, trace back to the producing state and run it first.