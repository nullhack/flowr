"""Tests for resolved output rule."""

import subprocess
import sys
import tempfile
from pathlib import Path

from flowr.domain.loader import load_flow
from flowr.domain.mermaid import to_mermaid


def test_named_condition_groups_a159b526() -> None:
    """
    Given a state defines conditions: {reviewed: {approved: "==true", score: ">=80"}}
    And a transition has when: [reviewed]
    When the user runs flowr check on the flow
    Then the output shows the transition guard as {approved: "==true", score: ">=80"}
    """
    yaml_str = """
flow: test
version: "1.0"
exits: [done]
states:
  - id: review
    conditions:
      reviewed:
        approved: "==true"
        score: ">=80"
    next:
      approve:
        to: done
        when: [reviewed]
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_str)
        f.flush()
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "flowr", "check", f.name, "review", "approve"],
            capture_output=True,
            text=True,
        )
    assert "approved" in result.stdout
    assert "==true" in result.stdout
    assert "score" in result.stdout
    assert ">=80" in result.stdout
    Path(f.name).unlink(missing_ok=True)


def test_named_condition_groups_6d5dddcc() -> None:
    """
    Given a state defines conditions: {reviewed: {approved: "==true"}}
    And a transition has when: [reviewed]
    When the user runs flowr mermaid on the flow
    Then the transition label shows approved: ==true
    """
    yaml_str = """
flow: test
version: "1.0"
exits: [done]
states:
  - id: review
    conditions:
      reviewed:
        approved: "==true"
    next:
      approve:
        to: done
        when: [reviewed]
"""
    flow = load_flow(yaml_str)
    diagram = to_mermaid(flow)
    assert "approved: ==true" in diagram
