"""Tests for validate command story."""

import json
import subprocess
import sys
from pathlib import Path

_YAML_VALID = """\
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

_YAML_MISSING_FIELDS = """\
flow: broken
version: "1.0"
exits: []
states: []
"""

_YAML_SHOULD_WARNING = """\
flow: test-flow
version: "1.0"
exits:
  - unreachable
states:
  - id: idle
    next:
      start:
        to: idle
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


def test_flowr_cli_f82e43f3(tmp_path: Path) -> None:
    """
    Given: a flow definition file that conforms to the specification
    When: the developer runs the validate command on that file
    Then: the output indicates the flow is valid
    """
    flow_file = _write_yaml(tmp_path, _YAML_VALID)
    result = _run_cli("validate", str(flow_file))
    assert result.returncode == 0
    assert "valid" in result.stdout.lower()


def test_flowr_cli_e60ea5d5(tmp_path: Path) -> None:
    """
    Given: a flow definition file missing required fields
    When: the developer runs the validate command on that file
    Then: the output lists at least one MUST-level violation
    """
    flow_file = _write_yaml(tmp_path, _YAML_MISSING_FIELDS)
    result = _run_cli("validate", str(flow_file))
    assert result.returncode == 1
    assert "MUST" in result.stdout


def test_flowr_cli_c74ff68e(tmp_path: Path) -> None:
    """
    Given: a flow definition file with a SHOULD-level issue
    When: the developer runs the validate command on that file
    Then: the output lists at least one SHOULD-level warning
    """
    flow_file = _write_yaml(tmp_path, _YAML_SHOULD_WARNING)
    result = _run_cli("validate", str(flow_file))
    assert "SHOULD" in result.stdout


def test_flowr_cli_25479a5b(tmp_path: Path) -> None:
    """
    Given: a flow definition file with violations
    When: the developer runs the validate command with --json on that file
    Then: the output is valid JSON containing the violation details
    """
    flow_file = _write_yaml(tmp_path, _YAML_MISSING_FIELDS)
    result = _run_cli("validate", str(flow_file), "--json")
    data = json.loads(result.stdout)
    assert "violations" in data
