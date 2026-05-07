Feature: Export Output Flag

  Add `--output` / `-o` flag to `flowr export` that writes export output to a file
  instead of stdout, with automatic `.js` wrapping for `file://` compatibility
  when combined with `--format json`. Wires `task regenerate-flowviz` to use
  the native export command, eliminating the need for a separate generation script.

  Status: ELICITING

  Rules (Business):
  - `--output` / `-o` flag writes export output to a file for all formats, creating parent directories as needed
  - When `--format json` and `--output` path ends in `.js`, the content is wrapped as `window.FLOWVIZ_DATA = <json>;` for `file://` compatibility
  - The `generate-flowviz-data.py` script is deleted; `app.js` handles the new JSON shape via its `transformFlow` function
  - `regenerate-flowviz` task added to pyproject.toml

  Constraints:
  - CLI exit codes: 0 = success, 1 = command failed, 2 = usage error (ADR_20260426_cli_io_convention)
  - Zero new runtime dependencies introduced
  - No changes to existing domain types (Flow, State, Transition, GuardCondition)
  - `.js` wrapping applies ONLY to JSON format — mermaid output with `.js` extension is written as-is without wrapping

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q1 | Should `.js` wrapping apply to all formats or only JSON? | Resolved | Only JSON — wrapping non-JSON (e.g. mermaid) as `window.FLOWVIZ_DATA = ...;` would produce invalid JavaScript |
  | Q2 | Should `--output` to an unwritable path produce exit code 1? | Resolved | Yes — OSError during write is caught and reported as exit code 1 |
  | Q3 | Should `--output` overwrite existing files? | Resolved | Yes — consistent with shell `>` redirection behavior |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-07 planning | — | Created: split from export-viz-pipeline (INVEST: must_examples <= 8) |

  Rule: Output-to-file via --output flag
    As a CLI user
    I want to write export output to a file via `--output` / `-o`
    So that scripted workflows (like `task regenerate-flowviz`) can produce output files directly without shell redirection

    @id:a7b9c1d3
    Example: --output writes to file instead of stdout
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format json --output /tmp/flowr-out.json examples/simple.yaml`
      Then the file `/tmp/flowr-out.json` contains valid JSON output and nothing is printed to stdout

    @id:b8c0d2e4
    Example: --output creates parent directories automatically
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format json --output /tmp/flowr/deep/nested/out.json examples/simple.yaml`
      Then the parent directories `/tmp/flowr/deep/nested/` are created and the file is written successfully

    @id:c9d1e3f5
    Example: --output works for all export formats
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format mermaid --output /tmp/flowr-out.mmd examples/simple.yaml`
      Then the file `/tmp/flowr-out.mmd` contains valid Mermaid stateDiagram-v2 output

  Rule: JavaScript wrapping for file:// compatibility
    As a tool author
    I want the `--output` flag to auto-wrap JSON output as a JavaScript variable assignment when the output file has a `.js` extension
    So that the D3 visualizer can load flow data from local files via the `file://` protocol without CORS restrictions

    @id:d0e2f4a6
    Example: .js extension wraps JSON as window.FLOWVIZ_DATA assignment
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format json --output .flowr/viz/data.js examples/simple.yaml`
      Then the file content starts with `window.FLOWVIZ_DATA = ` followed by the JSON object and ending with `;\n`

    @id:e1f3a5b7
    Example: .js wrapping does not apply to non-JSON formats
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format mermaid --output /tmp/out.js examples/simple.yaml`
      Then the file contains plain Mermaid output without `window.FLOWVIZ_DATA` wrapping

    @id:f2a4b6c8
    Example: Non-.js extension writes JSON without wrapping
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format json --output /tmp/out.json examples/simple.yaml`
      Then the file contains raw JSON without any JavaScript wrapping
