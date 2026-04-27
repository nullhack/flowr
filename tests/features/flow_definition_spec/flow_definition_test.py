"""Tests for flow definition story."""

from flowr.domain.flow_definition import Flow, State
from flowr.domain.validation import ConformanceLevel, validate


def test_flow_definition_spec_ccf4a4ba() -> None:
    """
    Given: a YAML document with flow, version, exits, and one state
    When: the validator loads the flow definition
    Then: the flow definition passes validation
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
    )
    result = validate(flow)
    assert result.is_valid


def test_flow_definition_spec_68055fed() -> None:
    """
    Given: a YAML document without the exits field
    When: the validator loads the flow definition
    Then: the validator reports a MUST-level error identifying the missing field
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


def test_flow_definition_spec_8360294d() -> None:
    """
    Given: a YAML document with flow, version, exits, and attrs but no states
    When: the validator loads the flow definition
    Then: the validator reports a MUST-level error identifying the missing states field
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[],
    )
    result = validate(flow)
    assert not result.is_valid
    assert any(
        v.severity == ConformanceLevel.MUST and "state" in v.message.lower()
        for v in result.errors
    )


def test_flow_definition_spec_cbf72d71() -> None:
    """
    Given: a YAML document with multiple states in order
    When: the validator loads the flow definition
    Then: the first state in the list is identified as the initial state
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(id="start"),
            State(id="middle"),
            State(id="end"),
        ],
    )
    assert flow.states[0].id == "start"
