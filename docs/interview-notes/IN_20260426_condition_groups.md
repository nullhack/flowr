# IN_20260426_condition_groups — Named condition groups specification

> **Status:** COMPLETE
> **Interviewer:** PO
> **Participant(s):** Stakeholder
> **Session type:** Feature specification

---

## Cross-cutting

| ID | Question | Answer |
|----|----------|--------|
| Q54 | Should flow-definition-spec validation rules be extended for the conditions field? | Yes, extend the flow-definition-spec validation. Bump a minor version. |
| Q55 | Should check display the resolved flat condition dict, the original named references, or both? | check displays the resolved flat condition dict. |
| Q56 | Should the Mermaid converter show named condition groups by name or as resolved conditions? | Mermaid shows resolved conditions (not named references). |
| Q57 | After inlining named references into a flat dict, does the closed evidence schema apply to the combined/resolved dict? | Yes, evidence must pass all the combined conditions for a state. |

## Feature: named-condition-groups

| ID | Question | Answer |
|----|----------|--------|
| Q58 | When a named reference and an inline dict in the same when list have overlapping keys, what happens? | Overlapping keys: later entries win. The when inline overrides the named reference's key. |
| Q59 | Can a named condition group reference another named group within the same conditions block? | No nesting — named groups cannot reference other named groups. Each group is a flat dict of condition expressions only. |
| Q60 | Can when contain multiple named references? | Yes, when can contain multiple named references and additional inline dicts. |
| Q61 | What happens if a state has an empty conditions block? | conditions is an optional keyword — useful when repeating conditions, but not required on every state. An empty block is valid but has no effect. |
| Q62 | What happens if a named condition group has an empty dict as its value? | Deferred to SA. |
| Q63 | Should the inlined result be visible to the user? | All conditions are flattened/combined. The user only sees the final list of conditions to verify. |
| Q64 | Should the validator check for unused named condition groups? | Deferred to SA. |
| Q65 | Pre-mortem: if a flow author writes when: reviewed (bare string), does it reference the named group? | when accepts three forms: bare dict (v1, unchanged), list (strings + inline dicts, AND-combined), and single string (shorthand for list with one named reference). when: reviewed is shorthand for when: [reviewed]. |

---

## Quality Attributes

| ID | Attribute | Scenario | Target | Priority |
|----|-----------|----------|--------|----------|
| QA6 | Backward Compatibility | When v1 flows with bare-dict when are loaded, they work unchanged | 100% backward compatible | Must |
| QA7 | Error Detection | When an unknown condition reference is used, a FlowParseError is raised | Zero unknown refs passing silently | Must |

---

## Pain Points Identified

- Repeating identical condition sets across multiple transitions is error-prone and hard to maintain

## Business Goals Identified

- Named condition groups allow flow authors to define reusable condition expressions at the state level

## Terms to Define (for glossary)

- Condition Inlining
- Condition Reference
- Named Condition Group

## Action Items

- [x] Record condition groups decisions
- [ ] SA to resolve deferred decisions (Q62, Q64)
- [ ] Write .feature file for named-condition-groups