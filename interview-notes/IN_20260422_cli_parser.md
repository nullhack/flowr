# IN_20260422_version_source — Version source decision

> **Status:** COMPLETE
> **Interviewer:** SA
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## General

| ID | Question | Answer |
|----|----------|--------|
| Q1 | How should the --version flag read the version string at runtime? | importlib.metadata.version() — stdlib canonical API for installed package metadata |
| Q2 | What about reading pyproject.toml directly with tomllib? | Works but requires file path resolution and I/O; importlib.metadata is simpler |
| Q3 | Should we expose a __version__ constant in flowr/__init__.py? | No — creates a second source of truth that still needs importlib.metadata or hardcoding to populate |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA1 | Correctness | When --version is invoked, the version string matches pyproject.toml exactly | 100% match | Must |

---

## Pain Points Identified

- Hardcoded version strings drift from pyproject.toml over time

## Business Goals Identified

- Single source of truth for version information

## Terms to Define (for glossary)

- Package Metadata

## Action Items

- [x] Record decision as ADR_20260422_version_source
- [ ] Implement version retrieval via importlib.metadata