# PM_20260502_feature-decomposition-overlap: Config shared between features, implemented without traceability

## Failed At

The `configurable-paths` feature (6 @id examples) is partially implemented despite never going through its own development cycle. Three of its six examples (`971ec591` — flows_dir from pyproject.toml, `5e0dd562` — default when no config, `076da303` — --flows-dir overrides config) are functionally complete because `cli-flow-name-resolution` needed `resolve_config()` and `--flows-dir` as infrastructure. The remaining three examples (`2e301322`, `36d41122`, `9d4c4973`) are for a `flowr config` subcommand that doesn't exist yet.

The feature file remains in `backlog/` with status `BASELINED`, giving the false impression that nothing has been built. Meanwhile, the code is on main, tested through other features' @id tags but untraced to configurable-paths.

## Root Cause

Feature decomposition at the specification stage did not enforce non-overlapping scope. When `cli-flow-name-resolution` was specified, it needed config resolution and a `--flows-dir` flag. Instead of declaring a dependency on `configurable-paths` and having that feature developed first, the `cli-flow-name-resolution` feature absorbed the shared capability into its own scope.

The flow's `create-py-stubs` and `write-bdd-features` steps generate stubs per feature in isolation. There is no cross-feature dependency check or overlap detection. Two features ended up with @id tags covering the same capability, traced to different test files, with no mechanism to link them.

## Missed Gate

The `specify-feature` and `write-bdd-features` steps should detect when a new feature's examples overlap with an existing feature's examples or already-implemented functionality. The `assess-architecture` step should flag when a feature depends on code that belongs to another feature's scope.

## Fix

### Short-term
- Split `configurable-paths.feature`: remove the 3 already-implemented examples (mark them as covered by cli-flow-name-resolution @id tags m3n4o5p6/q7r8s9t0), keep only the `flowr config` subcommand examples as a smaller feature
- Add a "Covered by" section to the feature file pointing to the implementing feature's @id tags

### Process
- During `specify-feature`, check if any example's capability is already implemented in the codebase or covered by another feature's @id tags
- During `write-bdd-features`, cross-reference new examples against existing feature files for overlap
- During `assess-architecture`, flag features that depend on capabilities owned by other features and declare explicit feature dependencies

## Restart Check

Before specifying a new feature, search the codebase and existing feature files for overlapping capabilities. If overlap is found, either extract the shared capability into its own feature (developed first) or declare an explicit dependency with traceability notes in both feature files.