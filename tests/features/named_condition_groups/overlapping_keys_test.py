"""Tests for overlapping keys rule."""

from flowr.domain.loader import load_flow


def test_named_condition_groups_959366c4() -> None:
    """
    Given a state defines conditions: {reviewed: {approved: "==true", score: ">=80"}}
    When a transition has when: [reviewed, {approved: "==false"}]
    Then the guard resolves to {approved: "==false", score: ">=80"}
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
      reject:
        to: done
        when: [reviewed, {approved: "==false"}]
"""
    flow = load_flow(yaml_str)
    transition = flow.states[0].next["reject"]
    assert transition.conditions is not None
    assert transition.conditions.conditions == {
        "approved": "==false",
        "score": ">=80",
    }
