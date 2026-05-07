# PM_20260507_cross-adapter-flags: Adapter-specific CLI flags visible for all formats

## Failed At

acceptance (delivery-flow) — adversarial dry-run: "flowr export --format mermaid --flat produces normal output with no indication that --flat was ignored. All adapter flags (--flat, --no-attrs, --no-conditions) appear in --help regardless of --format value."

## Root Cause

The export subcommand registers all adapter flags via a loop over EXPORTERS in `_add_subcommands()`, making every adapter's flags visible to every format. When a flag is parsed but the selected adapter doesn't consume it, argparse accepts it silently and the adapter ignores the unknown option key.

## Missed Gate

Design review (review-gate-flow) verified per-adapter flags were wired but did not test cross-adapter flag usage. The BDD scenarios `1d5ba172` and `0ce7099f` verify that correct flags appear in help for the matching format, but no scenario tests that incorrect flags are absent from help or rejected at runtime.

## Fix

Either:
1. Register adapter flags conditionally based on `--format` value (deferred parsing — two-pass argparse), or
2. Accept the current design and add a runtime warning when adapter options contain keys the adapter doesn't recognize, or
3. Document the behavior explicitly: "all flags are accepted; only those relevant to the selected format are used."

## Restart Check

After modifying adapter flag registration, verify: `flowr export --format mermaid --help` must NOT contain `--flat` or `--no-attrs`, OR the runtime must warn on unused flags.
