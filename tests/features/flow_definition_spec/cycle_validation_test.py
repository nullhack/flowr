"""Tests for cycle validation story."""

from flowr.domain.flow_definition import Flow, State, Transition
from flowr.domain.validation import ConformanceLevel, validate


def test_flow_definition_spec_7fe4a980() -> None:
    """
    Given: a flow where state discovery has a transition
      more-discovery targeting discovery itself
    When: the validator checks for cycles
    Then: the flow passes validation because within-flow cycles are allowed
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["complete"],
        states=[
            State(
                id="discovery",
                next={
                    "more-discovery": Transition(
                        trigger="more-discovery",
                        target="discovery",
                    ),
                    "done": Transition(
                        trigger="done",
                        target="complete",
                    ),
                },
            ),
        ],
    )
    result = validate(flow)
    assert result.is_valid


def test_flow_definition_spec_c4a19ac3() -> None:
    """
    Given: flow A invokes flow B as a subflow and flow B invokes flow A as a subflow
    When: the validator checks for cycles
    Then: the validator reports a MUST-level error for the cross-flow cycle
    """
    flow_a = Flow(
        flow="flow-a",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="start",
                flow="flow-b",
                next={
                    "complete": Transition(
                        trigger="complete",
                        target="done",
                    ),
                },
            ),
        ],
    )
    flow_b = Flow(
        flow="flow-b",
        version="1.0.0",
        exits=["complete"],
        states=[
            State(
                id="start",
                flow="flow-a",
                next={
                    "done": Transition(
                        trigger="done",
                        target="complete",
                    ),
                },
            ),
        ],
    )
    result = validate(flow_a, all_flows=[flow_a, flow_b])
    assert not result.is_valid
    assert any(
        v.severity == ConformanceLevel.MUST and "cycle" in v.message.lower()
        for v in result.errors
    )
