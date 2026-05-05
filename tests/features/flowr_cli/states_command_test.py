"""Tests for states command story."""

import json
import subprocess
import sys
from pathlib import Path

_YAML_THREE_STATES = """\
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
  - id: done
    next: {}
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


def test_flowr_cli_2faa93a6(tmp_path: Path) -> None:
    """
    Given: a flow definition with three states named idle, working, done
    When: the developer runs the states command on that file
    Then: the output contains all three state ids
    """
    flow_file = _write_yaml(tmp_path, _YAML_THREE_STATES)
    result = _run_cli("states", str(flow_file), "--text")
    assert result.returncode == 0
    assert "idle" in result.stdout
    assert "working" in result.stdout
    assert "done" in result.stdout


def test_flowr_cli_9b7eba0c(tmp_path: Path) -> None:
    """
    Given: a flow definition with multiple states
    When: the developer runs the states command (JSON is default)
    Then: the output is a valid JSON array of state ids
    """
    flow_file = _write_yaml(tmp_path, _YAML_THREE_STATES)
    result = _run_cli("states", str(flow_file))
    data = json.loads(result.stdout)
    assert isinstance(data, list)
    assert "idle" in data
    assert "working" in data
