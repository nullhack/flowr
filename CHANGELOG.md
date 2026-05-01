# Changelog

All notable changes to this project will be documented in this file.

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