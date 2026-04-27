"""Tests for session format story."""

from flowr.domain.session import Session, SessionStackFrame


def test_flow_definition_spec_33ace791() -> None:
    """
    Given: a session file with current flow: scope-cycle and current state: discovery
    When: the session is loaded
    Then: the current position in the workflow is identified as scope-cycle/discovery
    """
    session = Session(flow="scope-cycle", state="discovery")
    assert session.flow == "scope-cycle"
    assert session.state == "discovery"
    position = f"{session.flow}/{session.state}"
    assert position == "scope-cycle/discovery"


def test_flow_definition_spec_4354f16e() -> None:
    """
    Given: a session file with a stack containing the parent flow and state
    When: the session is loaded
    Then: the call stack correctly represents the subflow nesting depth
    """
    session = Session(
        flow="feature-flow",
        state="step-2-arch",
        stack=[
            SessionStackFrame(flow="feature-flow", state="step-1-scope"),
        ],
    )
    assert len(session.stack) == 1
    assert session.stack[0].flow == "feature-flow"
    assert session.stack[0].state == "step-1-scope"


def test_flow_definition_spec_7496768d() -> None:
    """
    Given: a valid session file
    When: the session format is validated
    Then: no transition count or history fields are present
    """
    session = Session(flow="scope-cycle", state="discovery")
    assert not hasattr(session, "transitions")
    assert not hasattr(session, "history")
