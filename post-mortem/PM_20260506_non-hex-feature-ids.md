# PM_20260506_non-hex-feature-ids: Subagent used sequential identifiers instead of 8-char hex @id tags

## Failed At

feature-examples (planning-flow) — PO subagent generated 17 `@id` tags using human-readable sequential format (`ecore-001`, `ejson-001`, `emmd-001`) instead of the project convention of 8-character lowercase hex strings (e.g., `8ababd33`). The stakeholder caught the violation during review.

## Root Cause

The orchestrator dispatched the PO subagent with generic instructions to "add `@id` tags (unique hex IDs)" but did not supply the `@id` convention specification. The subagent invented its own scheme — a human-readable prefix per feature file (`ecore-` for export-core, `ejson-` for export-json, `emmd-` for export-mermaid) plus a sequential number. This scheme:

1. **Violates the feature template.** The `.templates/docs/features/feature.feature.template` uses `@id:3a7f1b2c` (8-char hex) as its example. The subagent did not read the template before generating IDs.
2. **Introduces a naming convention not defined anywhere.** No project document specifies prefix-based ID schemes. The subagent fabricated a convention that conflicts with the established one.
3. **Creates coupling between ID and file name.** Prefixing `ecore-` ties the ID to the feature file name, making reorganization expensive and IDs non-portable.

## Missed Gate

The create-py-stubs skill and stub-design knowledge specify `test_<feature_stem>_<id>` naming for test stubs, where `<id>` comes from the feature file's `@id` tag. If the feature file uses `ecore-001`, the test function becomes `test_export_core_ecore_001`, which is redundant and violates the flat-namespace convention. The orchestrator did not validate the generated IDs against the template before accepting the subagent's output.

## Fix

When dispatching a subagent to produce or modify feature files:

1. Include the `@id` convention explicitly in the dispatch prompt: "8-character lowercase hex string, no prefixes, no sequential numbering."
2. After the subagent returns, validate all `@id` tags against the pattern `^[0-9a-f]{8}$` before transitioning.
3. Ensure the subagent reads the feature template (`.templates/docs/features/feature.feature.template`) before generating any IDs — the template contains the canonical example.

## Restart Check

After any subagent produces or modifies a `.feature` file, run: `grep -P '@id:(?![0-9a-f]{8}$)' docs/features/*.feature`. If any match is found, reject the output and require hex IDs before proceeding.
