"""Tests for CLI flow name resolution feature."""

import subprocess
import sys
from pathlib import Path

import pytest


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "flowr", *args],
        capture_output=True,
        text=True,
    )


def _write_yaml(tmp_path: Path, content: str, name: str) -> Path:
    p = tmp_path / name
    p.write_text(content)
    return p


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


@pytest.mark.skip(reason="not yet implemented")
def test_cli_flow_name_resolution_a1b2c3d4(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/feature-development-flow.yaml
    When the user runs flowr check feature-development-flow <state>
    Then the CLI resolves feature-development-flow to .flowr/flows/feature-development-flow.yaml and proceeds
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_cli_flow_name_resolution_e5f6g7h8(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/feature-development-flow.yaml
    When the user runs flowr check .flowr/flows/feature-development-flow.yaml <state>
    Then the CLI uses the path directly without name resolution (backward compatible)
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_cli_flow_name_resolution_i9j0k1l2(tmp_path: Path) -> None:
    """
    Given no YAML matching the name in flows_dir
    When the user runs flowr check nonexistent-flow <state>
    Then the CLI prints an error indicating the flow name and the configured flows_dir
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_cli_flow_name_resolution_m3n4o5p6(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with [tool.flowr] flows_dir = ".flowr/flows"
    And a flow YAML at custom/flows/my-flow.yaml
    When the user runs flowr check --flows-dir custom/flows my-flow <state>
    Then the CLI resolves my-flow to custom/flows/my-flow.yaml and proceeds
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_cli_flow_name_resolution_q7r8s9t0(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with [tool.flowr] flows_dir = ".flowr/flows"
    And a flow YAML at custom/flows/my-flow.yaml
    When the user runs flowr check custom/flows/my-flow.yaml <state>
    Then the CLI uses the file path directly (--flows-dir does not affect file paths)
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_cli_flow_name_resolution_u1v2w3x4(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/tdd-cycle-flow.yaml
    When the user runs flowr states tdd-cycle-flow
    Then the CLI resolves tdd-cycle-flow to .flowr/flows/tdd-cycle-flow.yaml
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_cli_flow_name_resolution_y5z6a7b8(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/tdd-cycle-flow.yaml
    When the user runs flowr states tdd-cycle-flow.yaml
    Then the CLI resolves tdd-cycle-flow.yaml by checking .flowr/flows/tdd-cycle-flow.yaml directly
    """
    raise NotImplementedError