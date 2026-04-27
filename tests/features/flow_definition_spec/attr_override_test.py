"""Tests for attr override story."""

from flowr.domain.flow_definition import Flow, State
from flowr.domain.validation import validate


def test_flow_definition_spec_a50ab6c3() -> None:
    """
    Given: a flow with attrs { timeout: 300, retry: 2 }
      and a state with attrs { timeout: 600, docker: true }
    When: the validator resolves the state attrs
    Then: the effective attrs are { timeout: 600, docker: true }
      with no retry key
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(id="start", attrs={"timeout": 600, "docker": True}),
        ],
        attrs={"timeout": 300, "retry": 2},
    )
    result = validate(flow)
    assert result.is_valid
    state_attrs = flow.states[0].attrs
    assert state_attrs is not None
    assert state_attrs == {"timeout": 600, "docker": True}
    assert "retry" not in state_attrs


def test_flow_definition_spec_13e298f1() -> None:
    """
    Given: a flow with attrs { owner: platform-team }
      and a state without attrs
    When: the validator resolves the state attrs
    Then: the state has no attrs
      (flow-level attrs are not inherited to states without attrs)
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
        attrs={"owner": "platform-team"},
    )
    result = validate(flow)
    assert result.is_valid
    assert flow.states[0].attrs is None
