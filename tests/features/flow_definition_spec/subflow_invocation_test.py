"""Tests for subflow invocation story."""

from flowr.domain.flow_definition import Flow, State, Transition
from flowr.domain.validation import ConformanceLevel, validate


def test_flow_definition_spec_bf07819e() -> None:
    """
    Given: a state with flow: scope-cycle and flow-version: "^1"
    When: the validator loads the flow definition
    Then: the state is recognized as a subflow invocation
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(id="start", flow="scope-cycle", flow_version="^1"),
        ],
    )
    assert flow.states[0].flow == "scope-cycle"
    assert flow.states[0].flow_version == "^1"


def test_flow_definition_spec_db51954e() -> None:
    """
    Given: a parent state invoking scope-cycle with next keys
      complete and blocked matching the child exits
    When: the validator checks the subflow contract
    Then: the subflow invocation passes validation
    """
    child = Flow(
        flow="scope-cycle",
        version="1.0.0",
        exits=["complete", "blocked"],
        states=[State(id="start")],
    )
    parent = Flow(
        flow="parent-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="invoke-child",
                flow="scope-cycle",
                flow_version="^1",
                next={
                    "complete": Transition(
                        trigger="complete",
                        target="done",
                    ),
                    "blocked": Transition(
                        trigger="blocked",
                        target="done",
                    ),
                },
            ),
        ],
    )
    result = validate(parent, all_flows=[parent, child])
    assert result.is_valid


def test_flow_definition_spec_e19a1a33() -> None:
    """
    Given: a parent state invoking scope-cycle with next key success
      that is not in the child exits
    When: the validator checks the subflow contract
    Then: the validator reports a MUST-level error for the mismatched exit
    """
    child = Flow(
        flow="scope-cycle",
        version="1.0.0",
        exits=["complete", "blocked"],
        states=[State(id="start")],
    )
    parent = Flow(
        flow="parent-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="invoke-child",
                flow="scope-cycle",
                flow_version="^1",
                next={
                    "success": Transition(
                        trigger="success",
                        target="done",
                    ),
                },
            ),
        ],
    )
    result = validate(parent, all_flows=[parent, child])
    assert not result.is_valid
    assert any(
        v.severity == ConformanceLevel.MUST and "does not match" in v.message.lower()
        for v in result.errors
    )
