# Changelog

All notable changes to this project will be documented in this file.

## [v0.1] - 2026-04-26

### Added

- **`flowr/__main__.py`**: CLI entrypoint — `python -m flowr --help` and `python -m flowr --version`; zero new dependencies (argparse + importlib.metadata are stdlib)
- **`docs/adr/ADR-2026-04-22-cli-parser-library.md`**: decision record for choosing `argparse` over click/typer
- **`docs/adr/ADR-2026-04-22-version-source.md`**: decision record for reading version from `importlib.metadata` at runtime
- **`docs/features/completed/cli-entrypoint.feature`**: completed feature file for CLI entrypoint
- **`docs/branding.md`**: project identity, colour palette, release naming convention, and wording guidelines
- **`docs/glossary.md`**: living glossary with domain terms
- **`docs/discovery.md`**: discovery session synthesis log
- **`docs/scope_journal.md`**: raw Q&A from discovery sessions
- **`docs/system.md`**: current-state architecture snapshot with domain model, C4 diagrams, and ADR index
- **`docs/index.html`**: documentation portal with branding palette, doc cards, tabbed features, ADR list, and research library
- **`scripts/`**: 10 validation and automation scripts (`assign_ids.py`, `check_adrs.py`, `check_commit_messages.py`, `check_feature_file.py`, `check_oc.py`, `check_stubs.py`, `check_version.py`, `check_work_md.py`, `detect_state.py`, `score_features.py`, `update_index_html.py`)
- **`.opencode/`**: agents, skills, and knowledge files for AI-assisted development workflow (product-owner, system-architect, software-engineer, designer, setup-project)
- **CI workflows**: `.github/workflows/ci.yml` (quality, test, build, publish-docs) and `.github/workflows/pypi-publish.yml` (PyPI release via OIDC)
- **`docs/research/`**: 11 scientific research files covering AI agents, architecture, cognitive science, documentation, domain modeling, OOP design, refactoring, requirements elicitation, software economics, testing, and version control
- **`docs/adr/ADR-2026-04-22-version-source.md`**: ADR template with interview Q&A and stakeholder validation gate
- **`tests/features/cli_entrypoint/`**: 3 test files covering 6 acceptance criteria via subprocess
- **`tests/unit/main_test.py`**: 5 in-process unit tests for 100% coverage

### Changed

- **Project initialised from temple8 template**: renamed to `flowr` — all references updated across `pyproject.toml`, README, CI workflows, tests, docs, scripts, and feature files