Feature: Remove Fuzzy Match (~=) Operator

  The `~=` (APPROXIMATELY_EQUAL) operator provides 5% tolerance numeric matching
  in guard conditions. It is unused in practice and adds unnecessary complexity
  to the specification and codebase. This feature removes it entirely from the
  flowr specification, reference implementation, tests, and documentation.

  Status: BASELINED (2026-05-06)

  Rules (Business):
  - The `~=` operator is not a valid condition operator in flowr v1
  - Flows containing `when: { field: "~=value" }` produce a validation error
  - The specification documents list exactly 6 operators: ==, !=, >=, <=, >, <

  Constraints:
  - Error messages follow existing FlowParseError conventions with location context

  ## Frozen Examples Rule

  After a feature is BASELINED, all `Example:` blocks are immutable. Changes require
  `@deprecated` on the old Example (preserving the original @id) and a new Example
  with a new @id. This prevents scope creep and maintains traceability.

  `@id` tags are for traceability only — do NOT add priority tags (e.g. @must, @should,
  @could) to Examples. MoSCoW classification is an internal triage step, not a Gherkin tag.

  ## Pre-mortem

  Imagine this feature was built and all tests pass, but it doesn't work for the user.

  | Failure Mode | Risk | Covered By |
  |-------------|------|------------|
  | `~=` silently accepted as bare string value (implicit `==`) instead of raising error | High — user gets no feedback that their flow is wrong | @id:7aef4c1b |
  | APPROXIMATELY_EQUAL member persists in ConditionOperator enum | Medium — dead code, potential future misuse | @id:3170064f |
  | Spec docs or glossary still list ~= as valid operator (e.g. Guard Condition entry) | Medium — contradicts implementation | @id:817a1558 |
  | ADR left without deprecation context — future readers don't know ~= was removed | Low — documentation hygiene | @id:452ceae3 |
  | Glossary "Fuzzy Match" entry not marked retired (append-only glossary) | Low — glossary convention, not operator table | In scope of implementation but not a separate Example; covered by 003's scope including glossary.md |

  All failure modes have corresponding Examples. No additional Examples needed.

  ## Questions

  | ID | Question | Status | Answer / Assumption |
  |----|----------|--------|---------------------|
  | Q1 | Should ~= produce a specific error or fall through to implicit ==? | Resolved | Clear parse error following FlowParseError convention |
  | Q2 | Should we supersede the ADR? | Resolved | Add deprecation note to existing ADR only |
  | Q3 | Should docs/index.html be updated? | Resolved | No, out of scope (already omits ~=) |

  ## Changes

  | Session | Q-IDs | Change |
  |---------|-------|--------|
  | 2026-05-06 S1 | Q1-Q3 | Created: remove ~= from code, tests, spec docs, ADR |

  Rule: Remove ~= operator from specification and implementation
    As a flow author
    I want the ~= operator removed from the flowr specification
    So that the specification is simpler with only operators I actually need

  @id:7aef4c1b
    Example: ~= operator is not recognized
      Given a flow file with `when: { score: "~=100" }`
      When the flow is loaded
      Then a FlowParseError is raised indicating ~= is not a valid operator

  @id:3170064f
    Example: ConditionOperator enum has 6 operators
      Given the ConditionOperator enum
      When its values are listed
      Then it contains exactly EQUALS, NOT_EQUALS, GREATER_THAN_OR_EQUAL, LESS_THAN_OR_EQUAL, GREATER_THAN, LESS_THAN
      And does not contain APPROXIMATELY_EQUAL

  @id:817a1558
    Example: Specification documents list 6 operators
      Given the specification documents (flow_definition_spec.md, glossary.md, product_definition.md)
      When the operator list is checked
      Then exactly 6 operators are listed: ==, !=, >=, <=, >, <
      And ~= does not appear in any operator table or definition

  @id:452ceae3
    Example: Fuzzy match ADR has deprecation note
      Given ADR_20260426_fuzzy_match_algorithm.md
      When the document is read
      Then a deprecation notice is present indicating ~= has been removed from the specification
