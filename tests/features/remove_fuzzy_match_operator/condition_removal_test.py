"""Tests for remove-fuzzy-match-operator feature — @id tags 001 and 002."""

import pytest


@pytest.mark.skip(reason="not yet implemented")
def test_remove_fuzzy_match_001() -> None:
    """
    Given a flow file with `when: { score: "~=100" }`
    When the flow is loaded
    Then a FlowParseError is raised indicating ~= is not a valid operator
    """


@pytest.mark.skip(reason="not yet implemented")
def test_remove_fuzzy_match_002() -> None:
    """
    Given the ConditionOperator enum
    When its values are listed
    Then it contains exactly EQUALS, NOT_EQUALS, GREATER_THAN_OR_EQUAL,
      LESS_THAN_OR_EQUAL, GREATER_THAN, LESS_THAN
    And does not contain APPROXIMATELY_EQUAL
    """
