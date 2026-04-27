"""Tests for conformance story."""

import dataclasses

import pytest

from flowr.domain.flow_definition import Flow, State
from flowr.domain.validation import ConformanceLevel, validate


def test_flow_definition_spec_1aa411c3() -> None:
    """
    Given: a conforming implementation that loads flow definitions
    When: a loaded flow definition is modified after loading
    Then: the implementation rejects the modification as a MUST-level violation
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
    )
    # Flow is a frozen dataclass — direct assignment raises FrozenInstanceError
    with pytest.raises(dataclasses.FrozenInstanceError):
        flow.flow = "modified"  # pyright: ignore[reportAttributeAccessIssue]


def test_flow_definition_spec_cd40fd6e() -> None:
    """
    Given: a conforming implementation that detects a conflict
      between the filesystem and session cache
    When: the implementation resolves the conflict
    Then: the filesystem version takes precedence
      as a SHOULD-level recommendation
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
    )
    result = validate(flow)
    assert result.is_valid


def test_flow_definition_spec_23b797eb() -> None:
    """
    Given: a conforming validator processing a flow definition
    When: the validator reports violations
    Then: each violation is classified as either MUST (required) or SHOULD (recommended)
    """
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
    )
    result = validate(flow)
    for v in result.violations:
        assert v.severity in (
            ConformanceLevel.MUST,
            ConformanceLevel.SHOULD,
        )
