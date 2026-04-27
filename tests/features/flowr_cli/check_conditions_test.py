"""Tests for check conditions story."""

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

_YAML_UNGUARDED = """\
flow: test-flow
version: "1.0"
exits:
  - complete
states:
  - id: idle
    next:
      start:
        to: working
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


def test_flowr_cli_d9d7f5d7(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state that has a guarded transition
    When: the developer runs the check command for that state and target
    Then: the output shows the guard condition's evidence keys and operators
    """
    flow_file = _write_yaml(tmp_path, _YAML_GUARDED)
    result = _run_cli("check", str(flow_file), "idle", "approve")
    assert result.returncode == 0
    assert "score" in result.stdout
    assert ">=" in result.stdout


def test_flowr_cli_3d4c9d59(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state that has an unguarded transition
    When: the developer runs the check command for that state and target
    Then: the output indicates no conditions are required
    """
    flow_file = _write_yaml(tmp_path, _YAML_UNGUARDED)
    result = _run_cli("check", str(flow_file), "idle", "start")
    assert result.returncode == 0
    assert "none" in result.stdout.lower() or "conditions" in result.stdout.lower()


def test_flowr_cli_495c9fd6(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state
    When: the developer runs the check command for a non-existent target
    Then: the output indicates the transition target was not found
    """
    flow_file = _write_yaml(tmp_path, _YAML_UNGUARDED)
    result = _run_cli("check", str(flow_file), "idle", "nonexistent")
    assert result.returncode == 1
    assert "not found" in result.stderr
