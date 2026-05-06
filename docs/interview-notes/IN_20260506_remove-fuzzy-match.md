# IN_20260506_remove-fuzzy-match — Remove ~= operator from specification

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## Feature: remove-fuzzy-match-operator

| ID | Question | Answer |
|----|----------|--------|
| Q1 | What is changing? | Complete removal of the `~=` (APPROXIMATELY_EQUAL) operator from the flowr specification and reference implementation. The 5% tolerance numeric matching operator will no longer be a valid condition operator. |
| Q2 | Why remove it? | Unused in practice. Adds complexity to the specification and codebase without providing value. The concept is over-engineered for what flowr needs. |
| Q3 | What defines success? | `~=` removed from: `ConditionOperator` enum, `_OPERATOR_PREFIXES` list, `_compare_numeric` function, all tests, spec docs (`flow_definition_spec.md`), glossary (`glossary.md`), system.md, product_definition.md. Existing ADR gets a deprecation note. Flows using `~=` produce a clear `FlowParseError` following current error conventions. |
| Q4 | How should flows using ~= fail? | Clearest approach using current conventions. The `FlowParseError` pattern (e.g. `f"Unknown condition reference '{name}'..."`) should be followed. After removal, `~=` will simply not be recognized as a valid operator prefix, so `parse_condition` will treat it as a bare value (implicit `==`). A validation-level check may be needed to catch it explicitly. |
| Q5 | What must never happen? | Silent acceptance of `~=` as a valid operator after removal. |
| Q6 | What about the ADR? | Add a deprecation note to `ADR_20260426_fuzzy_match_algorithm.md`. Do not supersede with a new ADR. |
| Q7 | What's out of scope? | `docs/index.html` is out of scope (already omits `~=`). No changes to the spec page. |

---

## Scope Confirmation

| Artifact | Action |
|----------|--------|
| `flowr/domain/condition.py` | Remove `APPROXIMATELY_EQUAL` enum, `"~="` from `_OPERATOR_PREFIXES`, `_compare_numeric` case |
| `tests/unit/condition_test.py` | Remove `~=` parse test (line 64) |
| `tests/features/.../condition_operators_test.py` | Remove/update `~=` feature tests (lines 68-122, including 2 skipped tests) |
| `docs/spec/flow_definition_spec.md` | Remove `~=` from operator table (line 250), examples (lines 85, 91), note (line 256), v1 scope (line 378) |
| `docs/spec/glossary.md` | Remove fuzzy-match term (lines 90-96), remove `~=` from guarded-transition definition (line 102) |
| `docs/spec/system.md` | Remove `~=` references (lines 137, 159, 195) |
| `docs/spec/product_definition.md` | Remove `~=` from expression list (line 18) |
| `docs/adr/ADR_20260426_fuzzy_match_algorithm.md` | Add deprecation note at top |
| `docs/index.html` | **Out of scope** (already omits `~=`) |
| `.flowr/flows/*.yaml` | No changes needed (no flows use `~=`) |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA1 | Correctness | When a flow file contains `when: { value: "~=100" }`, the validator rejects it | Clear error message following FlowParseError convention | Must |

---

## Action Items

- [ ] Write feature file with BDD scenarios covering code removal and doc updates
- [ ] Implement removal via TDD cycle
