"""Tests for CLI flow name resolution feature."""

import subprocess
import sys
from pathlib import Path

_YAML_FLOW = """\
flow: feature-development-flow
version: "1.0"
states:
  - id: idle
    next:
      start:
        to: step-1
  - id: step-1
"""

_YAML_FLOW_SIMPLE = """\
flow: my-flow
version: "1.0"
states:
  - id: start
    next:
      go: end
  - id: end
"""


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "flowr", *args]
    return subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _write_yaml(tmp_path: Path, content: str, name: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def _write_pyproject(tmp_path: Path, flows_dir: str = ".flowr/flows") -> Path:
    content = f"""\
[tool.flowr]
flows_dir = "{flows_dir}"
"""
    p = tmp_path / "pyproject.toml"
    p.write_text(content)
    return p


def test_cli_flow_name_resolution_a1b2c3d4(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/feature-development-flow.yaml
    When the user runs flowr check feature-development-flow <state>
    Then the CLI resolves feature-development-flow to
    .flowr/flows/feature-development-flow.yaml and proceeds
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    _write_yaml(tmp_path, _YAML_FLOW, ".flowr/flows/feature-development-flow.yaml")
    result = _run_cli("check", "feature-development-flow", "idle", cwd=str(tmp_path))
    assert result.returncode == 0
    assert "idle" in result.stdout


def test_cli_flow_name_resolution_e5f6g7h8(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/feature-development-flow.yaml
    When the user runs flowr check .flowr/flows/feature-development-flow.yaml <state>
    Then the CLI uses the path directly without name resolution (backward compatible)
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    _write_yaml(tmp_path, _YAML_FLOW, ".flowr/flows/feature-development-flow.yaml")
    result = _run_cli(
        "check", ".flowr/flows/feature-development-flow.yaml", "idle", cwd=str(tmp_path)
    )
    assert result.returncode == 0
    assert "idle" in result.stdout


def test_cli_flow_name_resolution_i9j0k1l2(tmp_path: Path) -> None:
    """
    Given no YAML matching the name in flows_dir
    When the user runs flowr check nonexistent-flow <state>
    Then the CLI prints an error indicating the flow name and the configured flows_dir
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    result = _run_cli("check", "nonexistent-flow", "idle", cwd=str(tmp_path))
    assert result.returncode == 1
    assert "nonexistent-flow" in result.stderr or "nonexistent-flow" in result.stdout


def test_cli_flow_name_resolution_m3n4o5p6(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with [tool.flowr] flows_dir = ".flowr/flows"
    And a flow YAML at custom/flows/my-flow.yaml
    When the user runs flowr check --flows-dir custom/flows my-flow <state>
    Then the CLI resolves my-flow to custom/flows/my-flow.yaml and proceeds
    """
    custom_dir = tmp_path / "custom" / "flows"
    custom_dir.mkdir(parents=True)
    _write_yaml(tmp_path, _YAML_FLOW_SIMPLE, "custom/flows/my-flow.yaml")
    result = _run_cli(
        "--flows-dir", "custom/flows", "check", "my-flow", "start", cwd=str(tmp_path)
    )
    assert result.returncode == 0
    assert "start" in result.stdout


def test_cli_flow_name_resolution_q7r8s9t0(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with [tool.flowr] flows_dir = ".flowr/flows"
    And a flow YAML at custom/flows/my-flow.yaml
    When the user runs flowr check custom/flows/my-flow.yaml <state>
    Then the CLI uses the file path directly (--flows-dir does not affect file paths)
    """
    custom_dir = tmp_path / "custom" / "flows"
    custom_dir.mkdir(parents=True)
    _write_yaml(tmp_path, _YAML_FLOW_SIMPLE, "custom/flows/my-flow.yaml")
    result = _run_cli("check", "custom/flows/my-flow.yaml", "start", cwd=str(tmp_path))
    assert result.returncode == 0
    assert "start" in result.stdout


def test_cli_flow_name_resolution_u1v2w3x4(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/tdd-cycle-flow.yaml
    When the user runs flowr states tdd-cycle-flow
    Then the CLI resolves tdd-cycle-flow to .flowr/flows/tdd-cycle-flow.yaml
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    yaml_content = """\
flow: tdd-cycle-flow
version: "1.0"
states:
  - id: red
    next:
      pass: green
  - id: green
"""
    _write_yaml(tmp_path, yaml_content, ".flowr/flows/tdd-cycle-flow.yaml")
    result = _run_cli("states", "tdd-cycle-flow", cwd=str(tmp_path))
    assert result.returncode == 0
    assert "red" in result.stdout


def test_cli_flow_name_resolution_y5z6a7b8(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/tdd-cycle-flow.yaml
    When the user runs flowr states tdd-cycle-flow.yaml
    Then the CLI resolves tdd-cycle-flow.yaml by checking
    .flowr/flows/tdd-cycle-flow.yaml directly
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    yaml_content = """\
flow: tdd-cycle-flow
version: "1.0"
states:
  - id: red
    next:
      pass: green
  - id: green
"""
    _write_yaml(tmp_path, yaml_content, ".flowr/flows/tdd-cycle-flow.yaml")
    result = _run_cli("states", "tdd-cycle-flow.yaml", cwd=str(tmp_path))
    assert result.returncode == 0
    assert "red" in result.stdout
