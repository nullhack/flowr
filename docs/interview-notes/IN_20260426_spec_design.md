# IN_20260426_spec_design — Flow specification design session

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Domain deep-dive

---

## General

| ID | Question | Answer |
|----|----------|--------|
| Q12 | Who are the users of the flow definition specification? (Re-asked: project scope has shifted from "Python project template" to "flow specification format") | Two user groups: developers/engineers who write and validate flow definitions, and tool authors who build tooling (validators, converters, editors) that consume the specification format. |
| Q13 | What does the product do at a high level? (Re-asked: the product is now a specification, not a template) | Three capabilities: define (YAML format for non-deterministic state machine workflows), validate (reference validator that checks conformance), and visualize (Mermaid converter that produces diagrams from flow definitions). |
| Q14 | Why does it exist — what problem does it solve? | No existing standard covers defining non-deterministic state machine workflows in YAML. Existing standards (XState, SCXML, etc.) don't address flowr's core features: per-state agent assignment, AI-agent-as-runtime, and filesystem-as-source-of-truth. |
| Q15 | When and where is it used? | Both humans and machines write and validate flows. Humans author flow YAML files; machines (validators, converters) parse and check them. |
| Q16 | Success — what does "done" look like for v1? | Three deliverables: prose specification document, reference validator (Python module), and Mermaid converter. No JSON Schema. |
| Q17 | Failure — what must never happen? | Ambiguity — the specification must not leave room for contradictory implementations. |
| Q18 | Out-of-scope for v1 — what are we explicitly not building? | No runtime engine and no session tracking in v1. |

## Specification Semantics

| ID | Question | Answer |
|----|----------|--------|
| Q19 | The spec says state-level attrs "override/extend" flow-level attrs. What are the merge semantics? | Replace entirely. State-level attrs completely replace flow-level attrs — no merge, no deep merge, no extension. |
| Q20 | The ~=value condition operator is defined as "approximate match". What's the exact matching rule? | **Revised at architecture:** The ~= operator applies ONLY to numeric values with 5% tolerance. String fuzzy matching was removed as too complicated. See ADR_20260426_fuzzy_match_algorithm. |
| Q21 | Does numeric extraction strip % from both condition value AND evidence value? | Yes. Numeric extraction strips from both condition AND evidence. |
| Q22 | What happens when a next target matches both a state id AND an exit name? | Validation error. A next target that matches both is ambiguous and must be rejected at load time. |
| Q23 | Are within-flow cycles allowed? | Within-flow cycles are allowed. Only cross-flow cycles (parent→child→parent) are forbidden. |
| Q24 | Can params have default values? | Params are declarations with optional default values. A param without a default value is required; missing required params are validation errors. |
| Q25 | Evidence values in conditions — are they typed? | **Resolved at architecture:** All evidence values are coerced to strings before comparison. YAML booleans become lowercase, YAML numbers become numeric strings. See ADR_20260426_evidence_type_system. |

## Validation & Conformance

| ID | Question | Answer |
|----|----------|--------|
| Q26 | Should v1 define conformance levels? | Yes. Two conformance levels: MUST (required for all conforming implementations) and SHOULD (recommended but not mandatory). |
| Q27 | Should v1 include a JSON Schema? | No JSON Schema. The prose specification plus the Python reference validator are sufficient. |
| Q28 | Should v1 include a reference validator implementation? | Yes — include a reference validator as a Python module. Part of the v1 deliverable. |
| Q29 | Should transition counts be tracked? | Remove transition counts from the v1 spec. They add complexity without clear value. |

## Feature: flow-definition-spec

| ID | Question | Answer |
|----|----------|--------|
| Q30 | What is the minimal v1 deliverable? | All deliverables: prose specification, Python reference validator, and Mermaid converter. JSON Schema removed per Q27. |
| Q31 | Should the existing flow YAML files serve as reference examples? | Yes. They are reference examples that v1 must validate correctly. |
| Q32 | Are immutable flows and filesystem truth behavioral requirements? | Immutable loaded flows is a MUST requirement. Filesystem truth is a SHOULD guideline. Session behavior is out of scope for v1. |
| Q33 | Should the specification use "flowr" branding? | Format-agnostic naming. The specification format has its own name independent of any implementation. |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA2 | Correctness | When a flow definition is validated, all MUST violations are reported | Zero false negatives on MUST rules | Must |
| QA3 | Unambiguity | When two conforming implementations interpret the same flow, they produce the same result | No contradictory interpretations | Must |
| QA4 | Extensibility | When a new condition operator is added, only the condition module changes | Single-module change | Should |

---

## Pain Points Identified

- No existing YAML standard covers non-deterministic state machine workflows with per-state agent assignment
- Existing standards (XState, SCXML) target execution engines, not specification/validation

## Business Goals Identified

- A declarative, validatable, toolable format for workflows that branch on evidence rather than control flow

## Terms to Define (for glossary)

- Flow Definition
- Flow Specification
- Guard Condition
- Evidence
- Exit
- Subflow
- Conformance
- Next Target Collision
- Cross-flow Cycle
- Within-flow Cycle
- Attrs
- Params
- Fuzzy Match
- Numeric Extraction

## Action Items

- [x] Record specification semantics decisions
- [ ] Write .feature file for flow-definition-spec
- [ ] Update glossary with new terms