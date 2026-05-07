Feature: Export Core

  Unified `flowr export --format <format>` command with format resolution, input validation,
  auto-detection of file vs directory, mermaid subcommand removal, and hardcoded registry.
  This is the foundation that export-json and export-mermaid build upon.

  Status: BASELINED (2026-05-06)

  Constraints:
  - Zero new runtime dependencies introduced
  - CLI exit codes: 0 = success, 1 = command failed, 2 = usage error (ADR_20260426_cli_io_convention)
  - CLI output: stdout for results, stderr for errors/warnings (ADR_20260426_cli_io_convention)
  - No modifications to existing domain types (Flow, State, Transition, GuardCondition) or loader functions
  - Extensibility: adding a new export format requires implementing the FlowExporter Protocol and registering in the EXPORTERS dict

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q1 | Should `--format` have a default value? | Resolved | `--format` is required — no default |
  | Q2 | Should unknown formats list available formats in the error? | Resolved | Yes — error message lists all registered format names |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-06 planning | — | Created: split from export.feature for INVEST compliance |

  Rule: Format resolution
    As a CLI user
    I want to specify an export format via `--format <name>`
    So that the system resolves the correct adapter before any file I/O occurs

    @id:8ababd33
    Example: Known format resolves successfully
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format json examples/simple.yaml`
      Then the command delegates to the json adapter with exit code 0

    @id:6c684a46
    Example: Unknown format fails fast
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format xml examples/simple.yaml`
      Then the command prints an error to stderr listing available formats and exits with code 1

    @id:43d8849f
    Example: Missing format flag produces usage error
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export examples/simple.yaml`
      Then the command prints a usage error to stderr and exits with code 2

  Rule: Input path validation
    As a CLI user
    I want the export command to validate that my input path exists
    So that I receive a clear error before any loading is attempted

    @id:d0169acb
    Example: Non-existent path produces error
      Given no file exists at `nonexistent.yaml`
      When the user runs `flowr export --format json nonexistent.yaml`
      Then the command prints an error to stderr stating the path does not exist and exits with code 1

  Rule: Auto-detect input type
    As a CLI user
    I want the export command to accept both files and directories
    So that I can export a single flow or a collection without specifying the mode explicitly

    @id:3c8f8a0a
    Example: File input triggers single-flow export
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format json examples/simple.yaml`
      Then the adapter's `export()` method is called with the loaded flow

    @id:e4152bc9
    Example: Directory input triggers collection export
      Given a directory `flows/` contains multiple `.yaml` files
      When the user runs `flowr export --format json flows/`
      Then the adapter's `export_directory()` method is called with all loaded flows sorted alphabetically by filename

  Rule: Mermaid subcommand removal
    As a CLI user
    I want `flowr mermaid` to be removed
    So that all export functionality is unified under a single subcommand

    @id:19cb145b
    Example: Mermaid subcommand no longer exists
      Given the flowr CLI is installed
      When the user runs `flowr mermaid examples/simple.yaml`
      Then the command prints a usage error to stderr and exits with code 2

  Rule: Hardcoded export registry
    As a tool author
    I want the export registry to be a hardcoded dict mapping format names to adapter instances
    So that the available formats are discoverable and predictable without runtime registration

    @id:dad5b532
    Example: Registry contains json and mermaid at module load
      Given the flowr package is imported
      Then the EXPORTERS dict contains keys `"json"` and `"mermaid"` mapping to their respective adapter instances
