"""Tests for transition command story."""

import json
import subprocess
import sys
from pathlib import Path

_YAML_GUARDED = """\
flow: test-flow
version: "1.0"
exits:
  - complete
states:
  - id: idle
    next:
      approve:
        to: working
        when:
          score: ">=80"
  - id: working
    next:
      finish:
        to: complete
"""

_YAML_SUBFLOW = """\
flow: parent-flow
version: "1.0"
exits:
  - complete
states:
  - id: idle
    next:
      start:
        to: review
  - id: review
    flow: child.yaml
    next:
      approved:
        to: complete
"""

_YAML_SUBFLOW_CHILD = """\
flow: child
version: "1.0"
exits:
  - approved
states:
  - id: entry
    next:
      approve:
        to: approved
"""


def _write_yaml(tmp_path: Path, content: str, name: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "flowr", *args],
        capture_output=True,
        text=True,
    )


def test_flowr_cli_0993f68a(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state that has a guarded transition
    When: the developer runs the transition command with a valid trigger and evidence
    Then: the output shows the target state
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED, "flow.yaml")
    result = _run_cli(
        "transition",
        str(flow_file),
        "idle",
        "approve",
        "--evidence",
        "score=90",
        "--text",
    )
    assert result.returncode == 0
    assert "working" in result.stdout


def test_flowr_cli_5302dfcf(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state that has a guarded transition
    When: the developer runs the transition command with failing evidence
    Then: the output indicates the transition is not valid
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED, "flow.yaml")
    result = _run_cli(
        "transition",
        str(flow_file),
        "idle",
        "approve",
        "--evidence",
        "score=30",
        "--text",
    )
    assert result.returncode == 1
    assert "not" in result.stderr.lower() or "not" in result.stdout.lower()


def test_flowr_cli_250c4dce(tmp_path: Path) -> None:
    """
    Given: a flow definition with a subflow state and the subflow file is available
    When: the developer runs the transition command targeting that subflow state
    Then: the output shows the first state of the referenced subflow
    """
    flow_file = _write_yaml(tmp_path, _YAML_SUBFLOW, "parent.yaml")
    _write_yaml(tmp_path, _YAML_SUBFLOW_CHILD, "child.yaml")
    result = _run_cli("transition", str(flow_file), "idle", "start", "--text")
    assert result.returncode == 0
    assert "review" in result.stdout or "child" in result.stdout


def test_flowr_cli_dac419ef(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state
    When: the developer runs the transition command with an invalid trigger
    Then: the output indicates the trigger was not found
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED, "flow.yaml")
    result = _run_cli("transition", str(flow_file), "idle", "nonexistent")
    assert result.returncode == 1
    assert "not found" in result.stderr


def test_flowr_cli_04589cee(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state and valid trigger and evidence
    When: the developer runs the transition command (JSON is default)
    Then: the output is valid JSON containing the next state
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED, "flow.yaml")
    result = _run_cli(
        "transition",
        str(flow_file),
        "idle",
        "approve",
        "--evidence",
        "score=90",
    )
    data = json.loads(result.stdout)
    assert "to" in data
    assert data["to"] == "working"
