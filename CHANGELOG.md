# Changelog

All notable changes to this project will be documented in this file.

## [v0.4.0+20260502] - Refined Semolina - 2026-05-02

### Added

- **CLI flow name resolution**: short flow names resolved from `.flowr/flows/` directory; file paths still work (backward compatible); `--flows-dir` global flag overrides `pyproject.toml` `flows_dir`; `FlowNameNotFoundError` with clear error messages
- **Session management**: `session init <flow>`, `session show`, `session set-state <state>`, `session list` subcommands; `--session [NAME]` flag on `transition`, `next`, and `check` for session-aware state resolution; `--format yaml|json` on session commands; subflow push/pop stack for nested workflow tracking; atomic session file writes (temp-file-then-rename); `SessionNameNotFoundError` for session path resolution mirroring flow name resolution pattern
- **Configurable paths**: `flowr config` subcommand showing resolved configuration keys with source provenance (default / pyproject.toml / CLI); `--json` flag for machine-readable output; `resolve_config_with_sources()` tracking where each value comes from
- **README rewrite**: clear purpose, audience (Agent Operators, Developers, Tool Authors), show-don't-tell examples, architecture section
- **Documentation portal**: role-based `docs/index.html` with Stakeholder / Architect / Engineer sections using flowr's bakery palette

### Changed

- **`flowr/infrastructure/config.py`**: extracted `_read_pyproject`, `_resolve_values`, `_resolve_sources`, `_to_config` helpers for reduced complexity
- **`flowr/domain/session.py`**: `SessionStore` Protocol moved to domain layer (hexagonal architecture); `push_stack()` accepts `new_flow` parameter; `pop_stack()` restores parent flow from stack frame; `datetime.UTC` replaces `timezone.utc`
- **`flowr/__main__.py`**: `--session` flag on `transition`/`next`/`check`; `session` subcommand group; `config` subcommand; `--flows-dir` as global flag (was per-subcommand); flow name resolution via `DefaultFlowNameResolver`; exit code 1 for `FlowNameNotFoundError` (was 2)
- **`flowr/cli/session_cmd.py`**: state validation on `set-state` (rejects invalid states); `--name` and `--session` accept both short names and file paths
- **100% test coverage** across all modules with `# pragma: no cover` for unreachable Protocol stubs, Python version fallbacks, and main() dispatch paths tested via subprocess integration tests

### Fixed

- **Exit code for flow name not found**: changed from 2 (usage error) to 1 (command failed) per ADR_20260426_cli_io_convention
- **`--flows-dir` flag scope**: moved from per-subcommand to global argument per technical design constraint
- **Convention violations from review**: `FlowNameNotFound` renamed to `FlowNameNotFoundError` (N818), added `__init__` docstring (D107), trailing newlines (W292), line length (E501), nested `with` combined (SIM117)

### Removed

- **`scripts/` directory**: all development scripts removed; `release-check` task now runs lint, static-check, test, and doc-build directly; `assign-ids` task removed

## [v0.3.20260427] - 2026-04-27 - Coarse Grind

### Fixed

- **Package build missing subpackages**: replaced static `packages = ["flowr"]` with `setuptools.packages.find` so `flowr.cli` and `flowr.domain` are included in the installed package
- **License deprecation**: changed `project.license` from TOML table `{ file = "LICENSE" }` to SPDX string `"MIT"` to eliminate setuptools deprecation warning
- **CI verification**: updated package install checks in both `ci.yml` and `pypi-publish.yml` to import all submodules (`flowr`, `flowr.cli`, `flowr.domain`)

## [v0.2.20260427] - 2026-04-27 - Whole Spelt

### Added

- **Flow definition spec**: full YAML specification with validation, guard conditions, subflows, attrs, params, cycles, and conformance levels
- **CLI**: six subcommands — `validate`, `states`, `check`, `next`, `transition`, `mermaid` — with `--json` output and `--evidence` flags
- **Named condition groups**: reusable condition expressions at state level, inlined at load time, with reference validation and unused-group warnings
- **Domain model**: `Flow`, `State`, `Transition`, `GuardCondition`, `ConditionExpression`, `Param`, `Session`, `SessionStack` as frozen dataclasses
- **Mermaid converter**: stateDiagram-v2 export with resolved conditions on transition labels
- **Validation engine**: MUST/SHOULD conformance levels, ambiguous target detection, cross-flow cycle detection, condition reference checks
- **6 ADRs**: evidence type system, fuzzy match algorithm, validation result, CLI I/O convention, subflow resolution, condition inlining, image rendering deferral
- **`docs/spec/flow_definition_spec.md`**: authoritative YAML format specification
- **`docs/spec/product_definition.md`**: product boundaries, users, and scope
- **Completed features**: `flow-definition-spec`, `flowr-cli`, `named-condition-groups`
- **Test suite**: feature tests and unit tests for all domain operations

### Changed

- **README.md**: removed redundant Flow Definition Format and Library Usage sections; added Documentation links to spec, system overview, and product definition
- **`docs/spec/product_definition.md`**: slimmed from 254 to 49 lines — removed duplicated technical reference content, kept only IS/IS NOT, Why, Users, Out of Scope, Delivery Order
- **Document cleanup**: removed `docs/discovery.md`, `FLOW.md`, `WORK.md`, `template-config.yaml`; consolidated provenance into `.feature` file `## Changes` sections
- **Version format**: switched to calver (`major.minor.YYYYMMDD`)

### Fixed

- **Lint and docstring fixes** from SA review of named-condition-groups

## [v0.1] - 2026-04-26

### Added

- **`flowr/__main__.py`**: CLI entrypoint — `python -m flowr --help` and `python -m flowr --version`; zero new dependencies (argparse + importlib.metadata are stdlib)
- **`docs/adr/ADR_20260422_cli_parser_library.md`**: decision record for choosing `argparse` over click/typer
- **`docs/adr/ADR_20260422_version_source.md`**: decision record for reading version from `importlib.metadata` at runtime
- **`docs/features/completed/cli-entrypoint.feature`**: completed feature file for CLI entrypoint
- **`docs/branding/branding.md`**: project identity, colour palette, release naming convention, and wording guidelines
- **`docs/spec/glossary.md`**: living glossary with domain terms
- **`docs/interview-notes/`**: interview notes from discovery sessions (replaces scope_journal.md)
- **`docs/spec/system.md`**: current-state architecture snapshot with domain model, C4 diagrams, and ADR index
- **`docs/index.html`**: documentation portal with branding palette, doc cards, tabbed features, ADR list, and research library
- **`scripts/`**: 10 validation and automation scripts (`assign_ids.py`, `check_adrs.py`, `check_commit_messages.py`, `check_feature_file.py`, `check_oc.py`, `check_stubs.py`, `check_version.py`, `check_work_md.py`, `detect_state.py`, `score_features.py`, `update_index_html.py`)
- **`.opencode/`**: agents, skills, and knowledge files for AI-assisted development workflow (product-owner, system-architect, software-engineer, designer, setup-project)
- **CI workflows**: `.github/workflows/ci.yml` (quality, test, build, publish-docs) and `.github/workflows/pypi-publish.yml` (PyPI release via OIDC)
- **`docs/research/`**: 11 scientific research files covering AI agents, architecture, cognitive science, documentation, domain modeling, OOP design, refactoring, requirements elicitation, software economics, testing, and version control
- **`docs/adr/ADR_20260422_version_source.md`**: ADR template with interview Q&A and stakeholder validation gate
- **`tests/features/cli_entrypoint/`**: 3 test files covering 6 acceptance criteria via subprocess
- **`tests/unit/main_test.py`**: 5 in-process unit tests for 100% coverage

### Changed

- **Project initialised from temple8 template**: renamed to `flowr` — all references updated across `pyproject.toml`, README, CI workflows, tests, docs, scripts, and feature files