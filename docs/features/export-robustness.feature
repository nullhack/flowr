Feature: Export Robustness

  Fixes three post-PR edge cases in the export command and CLI error handling:
  warns on unused adapter flags, rejects empty directories with exit code 1,
  and catches malformed YAML with user-friendly errors across all commands.

  Status: BASELINED (2026-05-07)

  Rules (Business):
  - When a user passes an adapter flag that the selected format does not consume, the CLI prints a warning to stderr listing the unused flag names
  - When a user exports from a directory containing no YAML flow files, the CLI prints an error to stderr and exits with code 1
  - When a user passes a malformed YAML file to any CLI command (validate, export, states, check, next, transition, session), the CLI prints a single-line error to stderr with no traceback and exits with code 1

  Constraints:
  - No new runtime dependencies
  - Error messages follow ADR_20260426_cli_io_convention (stderr for errors/warnings)
  - Exit codes follow ADR_20260426_cli_io_convention (0 = success, 1 = command failed)

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q1 | Should the unused-flag warning list flag names or just count? | Resolved | List flag names for clarity |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-07 IN_20260507 | — | Created: robustness fixes from post-PR adversarial dry-run |

  Rule: Unused adapter flag warning
    As a CLI user
    I want to be warned when I pass a flag irrelevant to my selected export format
    So that I don't silently get unexpected output

    @id:a1b2c3d4
    Example: JSON format with --no-conditions flag
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format json --no-conditions examples/simple.yaml`
      Then the command prints a warning to stderr containing "no-conditions" and exits with code 0

    @id:e5f6a7b8
    Example: Mermaid format with --flat flag
      Given a flow definition file exists at `examples/simple.yaml`
      When the user runs `flowr export --format mermaid --flat examples/simple.yaml`
      Then the command prints a warning to stderr containing "flat" and exits with code 0

  Rule: Empty directory rejection
    As a CLI user
    I want the export command to reject an empty directory with a clear error
    So that I know no flows were found instead of silently getting empty output

    @id:c9d0e1f2
    Example: Export from empty directory
      Given a directory exists at `/tmp/empty_flows` with no YAML files
      When the user runs `flowr export --format json /tmp/empty_flows`
      Then the command prints an error to stderr stating no flow files were found and exits with code 1

    @id:a3b4c5d6
    Example: Export from directory with only non-YAML files
      Given a directory exists at `/tmp/mixed` containing only `.txt` and `.json` files
      When the user runs `flowr export --format json /tmp/mixed`
      Then the command prints an error to stderr stating no flow files were found and exits with code 1

  Rule: Malformed YAML error handling
    As a CLI user
    I want malformed YAML files to produce a clean error message
    So that I never see a raw Python traceback from any command

    @id:e7f8a9b0
    Example: Malformed YAML with export command
      Given a file at `/tmp/bad.yaml` contains invalid YAML syntax
      When the user runs `flowr export --format json /tmp/bad.yaml`
      Then the command prints a single-line error to stderr with no traceback and exits with code 1

    @id:c1d2e3f4
    Example: Malformed YAML with validate command
      Given a file at `/tmp/bad.yaml` contains invalid YAML syntax
      When the user runs `flowr validate /tmp/bad.yaml`
      Then the command prints a single-line error to stderr with no traceback and exits with code 1
