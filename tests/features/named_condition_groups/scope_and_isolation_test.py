"""Tests for scope and isolation rule."""

import pytest

from flowr.domain.loader import FlowParseError, load_flow


def test_named_condition_groups_49a58755() -> None:
    """
    Given state A defines conditions: {reviewed: {approved: "==true"}}
    And state B has no conditions block
    When state B has a transition with when: [reviewed]
    Then the flow fails validation because reviewed is not defined in state B
    """
    yaml_str = """
flow: test
version: "1.0"
exits: [done]
states:
  - id: state-a
    conditions:
      reviewed:
        approved: "==true"
    next:
      go:
        to: state-b
        when: [reviewed]
  - id: state-b
    next:
      approve:
        to: done
        when: [reviewed]
"""
    with pytest.raises(FlowParseError, match="reviewed"):
        load_flow(yaml_str)
