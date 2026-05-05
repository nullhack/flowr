"""Tests for mermaid export story."""

import json
import subprocess
import sys
from pathlib import Path

_YAML_FLOW = """\
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


def test_flowr_cli_1bf637c4(tmp_path: Path) -> None:
    """
    Given: a flow definition with states and transitions
    When: the developer runs the mermaid command on that file
    Then: the output is a valid Mermaid stateDiagram-v2 string
    """
    flow_file = _write_yaml(tmp_path, _YAML_FLOW)
    result = _run_cli("mermaid", str(flow_file), "--text")
    assert result.returncode == 0
    assert "stateDiagram-v2" in result.stdout


def test_flowr_cli_8c9d008f(tmp_path: Path) -> None:
    """
    Given: a flow definition
    When: the developer runs the mermaid command (JSON is default)
    Then: the output is valid JSON containing the Mermaid diagram string
    """
    flow_file = _write_yaml(tmp_path, _YAML_FLOW)
    result = _run_cli("mermaid", str(flow_file))
    data = json.loads(result.stdout)
    assert "mermaid" in data
    assert "stateDiagram-v2" in data["mermaid"]
