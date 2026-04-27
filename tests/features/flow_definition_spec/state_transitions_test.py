"""Tests for state transitions story."""

from flowr.domain.condition import ConditionOperator, parse_condition
from flowr.domain.flow_definition import (
    Flow,
    GuardCondition,
    State,
    Transition,
)
from flowr.domain.validation import validate


def test_flow_definition_spec_730066c8() -> None:
    """
    Given: a state with next mapping go: done where done is an exit name
    When: the validator resolves the transition
    Then: the transition target resolves to the exit named done
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="start",
                next={
                    "go": Transition(trigger="go", target="done"),
                },
            ),
        ],
    )
    result = validate(flow)
    assert result.is_valid
    state = flow.states[0]
    assert "go" in state.next
    assert state.next["go"].target == "done"


def test_flow_definition_spec_01b2e389() -> None:
    """
    Given: a state with next mapping approve: { to: approved, when: { score: ">=80%" } }
    When: the validator loads the flow definition
    Then: the guarded transition is recognized with condition score >=80%
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["approved", "rejected"],
        states=[
            State(
                id="review",
                next={
                    "approve": Transition(
                        trigger="approve",
                        target="approved",
                        conditions=GuardCondition(
                            conditions={"score": ">=80%"},
                        ),
                    ),
                },
            ),
        ],
    )
    result = validate(flow)
    assert result.is_valid
    transition = flow.states[0].next["approve"]
    assert transition.conditions is not None
    assert transition.conditions.conditions["score"] == ">=80%"
    op, val = parse_condition(">=80%")
    assert op == ConditionOperator.GREATER_THAN_OR_EQUAL
    assert val == "80%"


def test_flow_definition_spec_eb8f6172() -> None:
    """
    Given: a state with next containing both simple and guarded transitions
    When: the validator loads the flow definition
    Then: both transition types are recognized in the same state
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["approved", "rejected"],
        states=[
            State(
                id="review",
                next={
                    "reject": Transition(
                        trigger="reject",
                        target="rejected",
                    ),
                    "approve": Transition(
                        trigger="approve",
                        target="approved",
                        conditions=GuardCondition(
                            conditions={"score": ">=80%"},
                        ),
                    ),
                },
            ),
        ],
    )
    result = validate(flow)
    assert result.is_valid
    simple = flow.states[0].next["reject"]
    guarded = flow.states[0].next["approve"]
    assert simple.conditions is None
    assert guarded.conditions is not None


def test_flow_definition_spec_78fa1402() -> None:
    """
    Given: a when condition with value pass (no operator prefix)
    When: the validator parses the condition
    Then: the condition is treated as ==pass
    """
    op, val = parse_condition("pass")
    assert op == ConditionOperator.EQUALS
    assert val == "pass"
