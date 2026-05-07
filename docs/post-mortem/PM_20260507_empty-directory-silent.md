# PM_20260507_empty-directory-silent: Exporting empty directory returns [] with exit code 0

## Failed At

acceptance (delivery-flow) — adversarial dry-run: "flowr export --format json /tmp/empty_flows outputs [] with exit code 0. No warning that the directory contained no flow files."

## Root Cause

`_load_flows_from_directory()` filters for `.yaml`/`.yml` files, loads each, and returns a list. When the directory contains no matching files, the list is empty. No code path checks whether the result is empty before proceeding.

## Missed Gate

The BDD scenario `e4152bc9` (directory input triggers collection export) tests a directory with YAML files present. No scenario tests an empty directory or a directory with only non-YAML files. The test suite verifies the happy path but not the zero-results edge case.

## Fix

In `_cmd_export`, after loading flows from a directory, check if the result is empty. If so, print a warning to stderr: "no flow files found in <path>" and either exit 0 (informational) or exit 1 (error). The stakeholder should decide which severity is appropriate.

## Restart Check

After fixing, verify: `flowr export --format json /tmp/empty_dir` must produce a message on stderr indicating no flows were found. The exit code must be documented in the feature file or ADR.
