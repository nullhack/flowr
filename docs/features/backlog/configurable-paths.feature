Feature: Configurable Paths for CLI

  The flowr CLI currently hardcodes the assumption that flow definition
  files live in `docs/flows/`. Users who organize their projects differently
  have no way to tell flowr where to find flow definitions. This feature
  adds a `[tool.flowr]` configuration section in `pyproject.toml` with a
  `flows_dir` key, a `--flows-dir` CLI flag to override the configured
  path, and a `flowr config` subcommand that prints the current resolved
  configuration.

  The library layer (`load_flow_from_file`, `resolve_subflows`) is
  unchanged — it takes explicit `Path` arguments and has no concept of
  configuration. Configuration is purely a CLI concern. The
  `flowr validate <file>` command continues to accept a direct file path
  with no name-based lookup.

  Three design decisions are deferred to the system-architect: exact
  default values for `flows_dir`, whether a session directory should be
  configurable, and how to handle misconfigured paths (non-existent
  directories, relative vs. absolute path resolution).

  Status: BASELINED (2026-04-26)

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-04-26 S5 | Q66–Q73 | Created: [tool.flowr] config section with flows_dir, --flows-dir CLI flag, flowr config subcommand; library unchanged; 3 SA-deferred decisions (defaults, session dir, misconfigured paths) |

  Rules (Business):
  - The CLI reads a `[tool.flowr]` section from `pyproject.toml` to resolve configuration values
  - The `flows_dir` configuration key specifies the directory containing flow definition YAML files
  - A `--flows-dir` CLI flag overrides the `pyproject.toml` value for a single invocation
  - A `flowr config` subcommand prints the current resolved configuration, showing each key, its value, and the source (default, pyproject.toml, or CLI flag)
  - Library functions (`load_flow_from_file`, `resolve_subflows`) remain unchanged — they take explicit Path arguments
  - The `flowr validate <file>` command continues to accept a direct file path; no name-based lookup is added
  - Only `flows_dir` is configurable in v1; session directory and other paths are not in scope

  Constraints:
  - Exact default values for `flows_dir` are deferred to the system-architect
  - Whether a session directory should be configurable is deferred to the system-architect
  - How to handle misconfigured paths (non-existent directories, relative vs. absolute resolution) is deferred to the system-architect
  - Configuration only affects the CLI layer; the library layer has no knowledge of configuration

  Rule: Pyproject configuration
    As a flowr user
    I want to configure the flows directory in pyproject.toml
    So that flowr respects my project structure without CLI flags on every invocation

    @id:971ec591
    Example: Flowr reads flows_dir from tool.flowr section
      Given a pyproject.toml with [tool.flowr] flows_dir = "src/flows"
      When the user runs any flowr CLI command
      Then the CLI resolves the flows directory to src/flows relative to the project root

    @id:5e0dd562
    Example: Missing tool.flowr section uses default
      Given a pyproject.toml with no [tool.flowr] section
      When the user runs any flowr CLI command
      Then the CLI uses the default flows directory

  Rule: CLI override
    As a flowr user
    I want to override the configured flows directory from the command line
    So that I can point to a different location for a single invocation

    @id:076da303
    Example: Dash-dash-flows-dir flag overrides pyproject.toml value
      Given a pyproject.toml with [tool.flowr] flows_dir = "src/flows"
      When the user runs flowr check --flows-dir other/flows
      Then the CLI uses other/flows instead of src/flows

  Rule: Config introspection
    As a flowr user
    I want a config subcommand that shows the resolved configuration
    So that I can verify which values are in effect and where they come from

    @id:2e301322
    Example: Config command shows resolved values and sources
      Given a pyproject.toml with [tool.flowr] flows_dir = "src/flows"
      When the user runs flowr config
      Then the output shows flows_dir = src/flows with source pyproject.toml

    @id:36d41122
    Example: Config command shows default source when no config exists
      Given a pyproject.toml with no [tool.flowr] section
      When the user runs flowr config
      Then the output shows flows_dir with its default value and source default

    @id:9d4c4973
    Example: Config command shows CLI flag as source when overridden
      Given a pyproject.toml with [tool.flowr] flows_dir = "src/flows"
      When the user runs flowr config --flows-dir other/flows
      Then the output shows flows_dir = other/flows with source cli