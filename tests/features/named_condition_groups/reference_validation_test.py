"""Tests for reference validation rule."""

import pytest

from flowr.domain.loader import FlowParseError, load_flow


def test_named_condition_groups_400fa5ad() -> None:
    """
    Given a state defines conditions: {reviewed: {approved: "==true"}}
    When a transition references when: [missing_ref]
    Then the flow fails validation with an error naming the unknown reference
    """
    yaml_str = """
flow: test
version: "1.0"
exits: [done]
states:
  - id: review
    conditions:
      reviewed:
        approved: "==true"
    next:
      approve:
        to: done
        when: [missing_ref]
"""
    with pytest.raises(FlowParseError, match="missing_ref"):
        load_flow(yaml_str)
