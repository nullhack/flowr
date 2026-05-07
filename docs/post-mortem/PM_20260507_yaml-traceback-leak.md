# PM_20260507_yaml-traceback-leak: Malformed YAML leaks raw Python traceback to user

## Failed At

acceptance (delivery-flow) — adversarial dry-run: "flowr export --format json /tmp/bad.yaml" and "flowr validate /tmp/bad.yaml" both crash with a full Python traceback (yaml.scanner.ScannerError) instead of a user-friendly error message.

## Root Cause

The CLI catches `FlowParseError` (raised by the loader when a valid YAML file lacks required fields) but not `yaml.scanner.ScannerError` or `yaml.parser.ParserError` (raised by PyYAML when the file is not valid YAML at all). These are different exception types at different layers: PyYAML raises scanner/parser errors during parsing, while `FlowParseError` is raised during semantic validation after successful parsing.

## Missed Gate

This is a pre-existing defect that predates the export feature. No existing BDD scenario tests malformed YAML input across any command. The test suite only covers: (1) valid flows, (2) semantically invalid flows (missing fields, bad transitions), and (3) non-existent paths. The "valid YAML syntax but invalid flow structure" case is covered; the "invalid YAML syntax" case is not.

## Fix

In `main()`, add a catch for `yaml.YAMLError` (parent of both `ScannerError` and `ParserError`) alongside the existing `FlowParseError` catch. Print a user-friendly message: "error: invalid YAML in <path>: <yaml error message>" with exit code 1. This fix applies to all commands that load YAML, not just export.

## Restart Check

After fixing, verify: `echo "not: valid: yaml: [{" > /tmp/bad.yaml && flowr export --format json /tmp/bad.yaml` must produce a single-line error on stderr with no traceback, exit code 1.
