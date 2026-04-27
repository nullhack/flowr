"""Tests for when forms rule."""

from flowr.domain.loader import load_flow


def test_named_condition_groups_615879b8() -> None:
    """
    Given a transition has when: {approved: "==true"}
    When the flow is loaded
    Then the guard is {approved: "==true"} with no named references
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
    transition = flow.states[0].next["approve"]
    assert transition.conditions is not None
    assert transition.conditions.conditions == {"approved": "==true"}
    assert transition.referenced_condition_groups is None


def test_named_condition_groups_b918281e() -> None:
    """
    Given a state defines conditions: {reviewed: {approved: "==true"}}
    When a transition has when: [reviewed, {retry_count: "<3"}]
    Then the guard resolves to {approved: "==true", retry_count: "<3"}
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
      retry:
        to: done
        when: [reviewed, {retry_count: "<3"}]
"""
    flow = load_flow(yaml_str)
    transition = flow.states[0].next["retry"]
    assert transition.conditions is not None
    assert transition.conditions.conditions == {
        "approved": "==true",
        "retry_count": "<3",
    }


def test_named_condition_groups_4c6f2f75() -> None:
    """
    Given a state defines conditions: {reviewed: {approved: "==true"}}
    When a transition has when: reviewed
    Then the guard resolves to {approved: "==true"}
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
        when: reviewed
"""
    flow = load_flow(yaml_str)
    transition = flow.states[0].next["approve"]
    assert transition.conditions is not None
    assert transition.conditions.conditions == {"approved": "==true"}
