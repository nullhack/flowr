Feature: CLI Flow Name Resolution

  The flowr CLI currently requires the `flow_file` positional argument to be
  an actual file path (e.g., `.flowr/flows/feature-development-flow.yaml`).
  Short flow names like `feature-development-flow` produce "File not found"
  errors even though the corresponding YAML exists in the configured
  `flows_dir`. This is a usability gap because the session store uses flow
  names, documentation references flow names, and agents naturally copy
  flow names from session YAML into CLI commands.

  This feature adds flow name resolution to the CLI layer: when the
  `flow_file` argument is not an existing file path, resolve it as a flow
  name by looking up `{flows_dir}/{flow_name}.yaml` using the same
  `resolve_config()` infrastructure introduced by the `configurable-paths`
  feature. A `--flows-dir` global CLI flag allows overriding the configured
  `flows_dir` for a single invocation.

  The library layer (`load_flow_from_file`, `resolve_subflows`) is
  unchanged — it takes explicit `Path` arguments and has no concept of
  configuration. Resolution happens in the CLI entrypoint before the
  file existence check.

  Status: BASELINED (2026-05-01)

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-01 S6 | Q74–Q86 | Created: flow name resolution as CLI-layer concern, file paths take priority, --flows-dir global flag, resolve_config() wiring, improved error messages |

  Rules (Business):
  - The CLI resolves the `flow_file` positional argument as either an existing file path or a flow name looked up in the configured `flows_dir`
  - When `flow_file` is an existing file path, it is used directly (backward compatible)
  - When `flow_file` is not an existing file path, the CLI resolves it as `{flows_dir}/{flow_name}.yaml` using `resolve_config()`
  - If the flow name has no `.yaml` extension, `.yaml` is appended during resolution
  - If the flow name already ends with `.yaml`, no additional extension is appended
  - A `--flows-dir` global CLI flag overrides the `pyproject.toml` `flows_dir` value for a single invocation
  - If neither a file path nor a flow name resolution succeeds, the CLI prints a clear error message indicating both the name and the configured `flows_dir`
  - Library functions (`load_flow_from_file`, `resolve_subflows`) remain unchanged — they take explicit `Path` arguments

  Constraints:
  - Flow name resolution is purely a CLI-layer concern — no library changes
  - This feature does not add session management or `--session` flags
  - The `--flows-dir` flag is a global argument, not per-subcommand

  Rule: Flow name resolution
    As a flowr user
    I want to use a flow name instead of a file path as the flow_file argument
    So that I can reference flows the same way the session store does

    @id:a1b2c3d4
    Example: Flow name resolves to file path
      Given a flow YAML at .flowr/flows/feature-development-flow.yaml
      When the user runs flowr check feature-development-flow <state>
      Then the CLI resolves feature-development-flow to .flowr/flows/feature-development-flow.yaml and proceeds

    @id:e5f6g7h8
    Example: Full file path still works
      Given a flow YAML at .flowr/flows/feature-development-flow.yaml
      When the user runs flowr check .flowr/flows/feature-development-flow.yaml <state>
      Then the CLI uses the path directly without name resolution (backward compatible)

    @id:i9j0k1l2
    Example: Flow name not found produces clear error
      Given no YAML matching the name in flows_dir
      When the user runs flowr check nonexistent-flow <state>
      Then the CLI prints an error indicating the flow name and the configured flows_dir

  Rule: Flows-dir override
    As a flowr user
    I want to override the flows directory from the command line
    So that I can point to a different location for a single invocation

    @id:m3n4o5p6
    Example: Dash-dash-flows-dir overrides config for flow name resolution
      Given a pyproject.toml with [tool.flowr] flows_dir = ".flowr/flows"
      And a flow YAML at custom/flows/my-flow.yaml
      When the user runs flowr check --flows-dir custom/flows my-flow <state>
      Then the CLI resolves my-flow to custom/flows/my-flow.yaml and proceeds

    @id:q7r8s9t0
    Example: Dash-dash-flows-dir overrides config for file path
      Given a pyproject.toml with [tool.flowr] flows_dir = ".flowr/flows"
      And a flow YAML at custom/flows/my-flow.yaml
      When the user runs flowr check custom/flows/my-flow.yaml <state>
      Then the CLI uses the file path directly (--flows-dir does not affect file paths)

  Rule: Extension handling
    As a flowr user
    I want flow names without .yaml to resolve correctly
    So that I can type the short form of a flow name

    @id:u1v2w3x4
    Example: Flow name without yaml extension resolves
      Given a flow YAML at .flowr/flows/tdd-cycle-flow.yaml
      When the user runs flowr states tdd-cycle-flow
      Then the CLI resolves tdd-cycle-flow to .flowr/flows/tdd-cycle-flow.yaml

    @id:y5z6a7b8
    Example: Flow name with yaml extension resolves
      Given a flow YAML at .flowr/flows/tdd-cycle-flow.yaml
      When the user runs flowr states tdd-cycle-flow.yaml
      Then the CLI resolves tdd-cycle-flow.yaml by checking .flowr/flows/tdd-cycle-flow.yaml directly