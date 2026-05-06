"""Tests for remove-fuzzy-match-operator feature."""

import pytest

from flowr.domain.condition import ConditionOperator
from flowr.domain.loader import FlowParseError, load_flow


def test_remove_fuzzy_match_operator_7aef4c1b() -> None:
    """
    Given: a flow file with `when: { score: "~=100" }`
    When: the flow is loaded
    Then: a FlowParseError is raised indicating ~= is not a valid operator
    """
    yaml_str = """\
flow: test
version: "1.0"
exits:
  - done
states:
  - id: idle
    next:
      proceed:
        to: done
        when:
          score: "~=100"
"""
    with pytest.raises(FlowParseError, match="~="):
        load_flow(yaml_str)


def test_remove_fuzzy_match_operator_3170064f() -> None:
    """
    Given: the ConditionOperator enum
    When: its values are listed
    Then: it contains exactly EQUALS, NOT_EQUALS, GREATER_THAN_OR_EQUAL,
      LESS_THAN_OR_EQUAL, GREATER_THAN, LESS_THAN
      And does not contain APPROXIMATELY_EQUAL
    """
    expected = {
        "EQUALS",
        "NOT_EQUALS",
        "GREATER_THAN_OR_EQUAL",
        "LESS_THAN_OR_EQUAL",
        "GREATER_THAN",
        "LESS_THAN",
    }
    actual = {op.name for op in ConditionOperator}
    assert actual == expected
    assert not hasattr(ConditionOperator, "APPROXIMATELY_EQUAL")
