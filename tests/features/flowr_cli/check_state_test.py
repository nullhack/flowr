"""Tests for check state story."""

import json
import subprocess
import sys
from pathlib import Path

_YAML_WITH_ATTRS = """\
flow: test-flow
version: "1.0"
exits:
  - complete
states:
  - id: idle
    attrs:
      color: blue
    next:
      start:
        to: working
  - id: working
    next:
      finish:
        to: complete
"""

_YAML_WITH_SUBFLOW = """\
flow: test-flow
version: "1.0"
exits:
  - complete
states:
  - id: idle
    flow: subflow.yaml
    next:
      done:
        to: complete
"""

_YAML_BASIC = """\
flow: test-flow
version: "1.0"
exits:
  - complete
states:
  - id: idle
    next:
      start:
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


def test_flowr_cli_92de4c71(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state that has attrs and transitions
    When: the developer runs the check command for that state
    Then: the output includes the state's attrs and available transitions
    """
    flow_file = _write_yaml(tmp_path, _YAML_WITH_ATTRS)
    result = _run_cli("check", str(flow_file), "idle", "--text")
    assert result.returncode == 0
    assert "color" in result.stdout
    assert "start" in result.stdout


def test_flowr_cli_155a7306(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state that references a subflow
    When: the developer runs the check command for that state
    Then: the output includes the referenced subflow name
    """
    flow_file = _write_yaml(tmp_path, _YAML_WITH_SUBFLOW)
    result = _run_cli("check", str(flow_file), "idle", "--text")
    assert result.returncode == 0
    assert "subflow.yaml" in result.stdout


def test_flowr_cli_0cf36941(tmp_path: Path) -> None:
    """
    Given: a flow definition with a state
    When: the developer runs the check command for that state (JSON is default)
    Then: the output is valid JSON containing the state details
    """
    flow_file = _write_yaml(tmp_path, _YAML_BASIC)
    result = _run_cli("check", str(flow_file), "idle")
    data = json.loads(result.stdout)
    assert "id" in data
    assert data["id"] == "idle"


def test_flowr_cli_e40ccf95(tmp_path: Path) -> None:
    """
    Given: a flow definition
    When: the developer runs the check command for a state that does not exist
    Then: the output indicates the state was not found
    """
    flow_file = _write_yaml(tmp_path, _YAML_BASIC)
    result = _run_cli("check", str(flow_file), "nonexistent")
    assert result.returncode == 1
    assert "not found" in result.stderr
