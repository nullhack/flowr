"""Tests for exit contract story."""

from flowr.domain.flow_definition import Flow, State, Transition
from flowr.domain.validation import ConformanceLevel, validate


def test_flow_definition_spec_2286f192() -> None:
    """
    Given: a YAML document without the exits field
    When: the validator loads the flow definition
    Then: the validator reports a MUST-level error for the missing exits
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=[],
        states=[State(id="start")],
    )
    result = validate(flow)
    assert not result.is_valid
    assert any(
        v.severity == ConformanceLevel.MUST and "exit" in v.message.lower()
        for v in result.errors
    )


def test_flow_definition_spec_c513f294() -> None:
    """
    Given: a parent state invoking a subflow with exits [complete, blocked]
    When: the parent state defines next keys [complete, blocked]
    Then: the subflow contract passes validation
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


def test_flow_definition_spec_c5bb3397() -> None:
    """
    Given: a flow with exits [done] where no state references done in any next mapping
    When: the validator checks exit references
    Then: the validator reports a SHOULD-level warning for the unreferenced exit
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
    )
    result = validate(flow)
    assert result.is_valid
    assert any(
        v.severity == ConformanceLevel.SHOULD and "not referenced" in v.message.lower()
        for v in result.warnings
    )
