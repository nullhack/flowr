"""Tests for mermaid conversion story."""

from flowr.domain.flow_definition import Flow, State, Transition
from flowr.domain.mermaid import to_mermaid


def test_flow_definition_spec_9540cdc3() -> None:
    """
    Given: a valid flow definition with states and transitions
    When: the Mermaid converter processes the flow
    Then: the output is a valid Mermaid stateDiagram-v2 diagram
      representing all states and transitions
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="start",
                next={
                    "go": Transition(trigger="go", target="end"),
                },
            ),
            State(id="end"),
        ],
    )
    output = to_mermaid(flow)
    assert "stateDiagram-v2" in output
    assert "start" in output
    assert "end" in output


def test_flow_definition_spec_82915538() -> None:
    """
    Given: a flow definition containing a subflow invocation
    When: the Mermaid converter processes the flow
    Then: the subflow state is represented with a reference to the invoked flow name
    """
    flow = Flow(
        flow="parent-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="invoke-child",
                flow="scope-cycle",
                next={
                    "complete": Transition(
                        trigger="complete",
                        target="done",
                    ),
                },
            ),
        ],
    )
    output = to_mermaid(flow)
    assert "scope-cycle" in output
