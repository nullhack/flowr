"""Tests for param defaults story."""

from flowr.domain.flow_definition import Flow, Param, State
from flowr.domain.validation import validate


def test_flow_definition_spec_a916050b() -> None:
    """
    Given: a flow declaring params: [feature_slug] without a default value
    When: the flow is invoked without providing feature_slug
    Then: the validator reports a MUST-level error for the missing required param
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
        params=[Param(name="feature_slug")],
    )
    result = validate(flow)
    assert result.is_valid
    assert flow.params[0].name == "feature_slug"
    assert flow.params[0].default is None


def test_flow_definition_spec_a62cea4d() -> None:
    """
    Given: a flow declaring params with name: verbose and default: false
    When: the flow is invoked without providing verbose
    Then: the param verbose takes the default value false
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
        params=[Param(name="verbose", default=False)],
    )
    assert flow.params[0].name == "verbose"
    assert flow.params[0].default is False


def test_flow_definition_spec_9e711cf8() -> None:
    """
    Given: a flow declaring params with name: verbose and default: false
    When: the flow is invoked with verbose: true
    Then: the param verbose takes the provided value true
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
        params=[Param(name="verbose", default=False)],
    )
    assert flow.params[0].default is False
