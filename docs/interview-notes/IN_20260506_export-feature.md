# IN_20260506_export-feature — Pluggable export adapters for flowr

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## Pain Points

1. **No export command.** flowr can validate, query, and generate Mermaid diagrams, but has no structured output format for external tooling (visualizers, analyzers, CI integrations). Tools must parse raw YAML and duplicate flowr's resolution logic.
2. **Mermaid is a standalone command.** `flowr mermaid` is a one-off subcommand, not part of a cohesive export system. Adding new formats means adding new subcommands with no shared pattern.
3. **No directory-level export.** Cannot export all flows from `.flowr/flows/` with cross-references resolved. Each flow must be exported individually.
4. **Issue #3 open.** The community has requested `flowr export --json` with a detailed proposal including JSON schema and use cases.

## Business Goals

1. Replace `flowr mermaid` with a unified `flowr export --format <format>` command backed by a pluggable adapter architecture.
2. Ship two built-in adapters: JSON (structured nodes/edges) and Mermaid (stateDiagram-v2).
3. Each adapter defines its own options (per-adapter CLI flags via `add_arguments()`).
4. Auto-detect file vs directory input — single flow export or multi-flow collection export.
5. Hardcoded registry for built-in formats (no entry points complexity). Third-party extensibility can be added later.

## Terms to Define

| Term | Definition |
|------|------------|
| **FlowExporter** | Protocol defining the adapter contract: `export()`, `export_directory()`, `format_name()`, `description()`, `supports_directory()`, `add_arguments()` |
| **ExportOptions** | Per-adapter options parsed from adapter-specific CLI flags (e.g. `--flat` for JSON, `--no-conditions` for Mermaid) |
| **Registry** | Hardcoded `EXPORTERS` dict mapping format name strings to FlowExporter instances |
| **Adapter** | A concrete implementation of the FlowExporter Protocol for a specific output format |
| **Directory mode** | Loading all YAML files from a directory, resolving subflow cross-references, and exporting as a collection |
| **Flat mode** | Flattening subflows into the parent flow's output rather than keeping them as separate entries |

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA1 | Extensibility | A developer wants to add a new export format | Implement FlowExporter Protocol, register in EXPORTERS dict, CLI auto-discovers it | Must |
| QA2 | Adapter autonomy | JSON adapter needs `--flat` flag, Mermaid doesn't | Each adapter adds its own arguments via `add_arguments()` | Must |
| QA3 | Auto-detection | User passes a directory instead of a file | All YAML files loaded, subflows resolved, exported as collection | Must |
| QA4 | Backward compatibility | Existing `flowr mermaid` users | `flowr mermaid` removed entirely; `flowr export --format mermaid` replaces it | Must |
| QA5 | Correctness | JSON export must resolve named condition groups | Named refs expanded into flat condition dicts; consumers don't need to understand resolution logic | Must |
| QA6 | Zero new dependencies | Built-in adapters ship with core | No new pip dependencies for JSON or Mermaid export | Must |
| QA7 | Test coverage | 100% coverage maintained | All new code covered, `mermaid` subcommand removal tested | Must |

---

## Adapter Specification

### JsonExporter

- **Subflow handling:** Nested by default — subflows appear as separate flow entries in the collection. `--flat` option inlines subflow states into the parent.
- **Directory mode:** Yes. Exports all flows as a collection with `defaultFlow` key.
- **Own flags:** `--flat`, `--no-attrs`
- **Output schema:** Follows the schema proposed in issue #3 (nodes with type state/subflow/exit, edges with kind transition/exit, resolved conditions, opaque attrs).

### MermaidExporter

- **Subflow handling:** Always flat — one stateDiagram-v2 per flow. Subflow references appear as notes.
- **Directory mode:** Yes. One diagram per flow, separated by `---`.
- **Own flags:** `--no-conditions`
- **Output:** Delegates to existing `to_mermaid()` in `flowr/domain/mermaid.py`.

---

## Scope Confirmation

| Artifact | Action |
|----------|--------|
| `flowr/domain/export.py` | New — FlowExporter Protocol |
| `flowr/exporters/__init__.py` | New — hardcoded EXPORTERS registry + `get_exporter()` |
| `flowr/exporters/json_exporter.py` | New — JsonExporter |
| `flowr/exporters/mermaid_exporter.py` | New — MermaidExporter (wraps `to_mermaid()`) |
| `flowr/__main__.py` | Add `export` subcommand, remove `mermaid` subcommand |
| `flowr/domain/mermaid.py` | Keep as-is (MermaidExporter delegates to it) |
| `tests/` | New tests per adapter, CLI integration tests, mermaid removal test |

## Action Items

- [ ] Transition stakeholder-interview with appropriate trigger
- [ ] Continue through discovery flow (event-storming, language, domain model, scope)
- [ ] Continue through architecture, planning, and development flows
