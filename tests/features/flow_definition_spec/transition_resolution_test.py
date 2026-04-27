"""Tests for transition resolution story."""

from flowr.domain.flow_definition import Flow, State, Transition
from flowr.domain.validation import ConformanceLevel, validate


def test_flow_definition_spec_77b26097() -> None:
    """
    Given: a next target step-2 that matches a state id but not an exit name
    When: the validator resolves the target
    Then: the target resolves to the state with id step-2
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="step-1",
                next={
                    "next": Transition(
                        trigger="next",
                        target="step-2",
                    ),
                },
            ),
            State(id="step-2"),
        ],
    )
    result = validate(flow)
    assert result.is_valid
    assert flow.states[0].next["next"].target == "step-2"


def test_flow_definition_spec_696085fd() -> None:
    """
    Given: a next target done that matches an exit name but not a state id
    When: the validator resolves the target
    Then: the target resolves to the exit named done
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


def test_flow_definition_spec_e60b9e41() -> None:
    """
    Given: a next target complete that matches both a state id and an exit name
    When: the validator resolves the target
    Then: the validator reports a MUST-level error for the ambiguous reference
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["complete"],
        states=[
            State(
                id="start",
                next={
                    "finish": Transition(
                        trigger="finish",
                        target="complete",
                    ),
                },
            ),
            State(id="complete"),
        ],
    )
    result = validate(flow)
    assert not result.is_valid
    assert any(
        v.severity == ConformanceLevel.MUST and "ambiguous" in v.message.lower()
        for v in result.errors
    )


def test_flow_definition_spec_f55badc3() -> None:
    """
    Given: a next target nonexistent that matches neither a state id nor an exit name
    When: the validator resolves the target
    Then: the validator reports a MUST-level error for the unresolvable target
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="start",
                next={
                    "go": Transition(
                        trigger="go",
                        target="nonexistent",
                    ),
                },
            ),
        ],
    )
    result = validate(flow)
    assert not result.is_valid
    assert any(
        v.severity == ConformanceLevel.MUST and "does not match" in v.message.lower()
        for v in result.errors
    )
