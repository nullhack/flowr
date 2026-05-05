"""Tests for next command story."""

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
      reject:
        to: idle
  - id: working
    next:
      finish:
        to: complete
"""


def _write_yaml(tmp_path: Path, content: str, name: str = "flow.yaml") -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "flowr", *args],
        capture_output=True,
        text=True,
    )


def test_flowr_cli_e0a380b7(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state that has a guarded transition
    When: the developer runs the next command with matching evidence
    Then: the output shows that transition as open (not blocked)
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED)
    result = _run_cli(
        "next", str(flow_file), "idle", "--evidence", "score=90", "--text"
    )
    assert result.returncode == 0
    assert "working" in result.stdout
    assert "[blocked]" not in result.stdout


def test_flowr_cli_79a29725(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state that has a guarded transition
    When: the developer runs the next command with non-matching evidence
    Then: the output shows the guarded transition as blocked
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED)
    result = _run_cli(
        "next", str(flow_file), "idle", "--evidence", "score=30", "--text"
    )
    assert result.returncode == 0
    assert "working" in result.stdout
    assert "[blocked]" in result.stdout


def test_flowr_cli_81dc8827(tmp_path: Path) -> None:
    """
    Given: a flow with both guarded and unguarded transitions from a state
    When: the developer runs the next command without providing evidence
    Then: the output shows all transitions with the guarded one marked blocked
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED)
    result = _run_cli("next", str(flow_file), "idle", "--text")
    assert result.returncode == 0
    assert "idle" in result.stdout
    assert "working" in result.stdout
    assert "[blocked]" in result.stdout


def test_flowr_cli_0b719a77(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state and valid evidence
    When: the developer runs the next command (JSON is default)
    Then: the output is valid JSON with transitions array of objects
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED)
    result = _run_cli("next", str(flow_file), "idle", "--evidence", "score=90")
    data = json.loads(result.stdout)
    assert "transitions" in data
    assert len(data["transitions"]) > 0
    for t in data["transitions"]:
        assert "trigger" in t
        assert "target" in t
        assert "status" in t
        assert "conditions" in t
