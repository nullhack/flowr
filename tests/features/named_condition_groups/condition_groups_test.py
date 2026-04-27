"""Tests for condition groups rule."""

from flowr.domain.loader import load_flow
from flowr.domain.validation import validate


def test_named_condition_groups_3850fde9() -> None:
    """
    Given a state defines conditions: {reviewed: {approved: "==true", score: ">=80"}}
    When a transition references reviewed via when: [reviewed]
    Then the transition's guard resolves to {approved: "==true", score: ">=80"}
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
        score: ">=80"
    next:
      approve:
        to: done
        when: [reviewed]
"""
    flow = load_flow(yaml_str)
    transition = flow.states[0].next["approve"]
    assert transition.conditions is not None
    assert transition.conditions.conditions == {"approved": "==true", "score": ">=80"}


def test_named_condition_groups_70c89435() -> None:
    """
    Given a state has no conditions field
    When a transition uses when: {approved: "==true"}
    Then the flow validates and loads exactly as v1
    """
    yaml_str = """
flow: test
version: "1.0"
exits: [done]
states:
  - id: review
    next:
      approve:
        to: done
        when: {approved: "==true"}
"""
    flow = load_flow(yaml_str)
    result = validate(flow)
    assert result.is_valid
    transition = flow.states[0].next["approve"]
    assert transition.conditions is not None
    assert transition.conditions.conditions == {"approved": "==true"}
