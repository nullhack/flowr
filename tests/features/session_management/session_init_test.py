"""Tests for session init rule — @id tags a1b2c3d4 and i9j0k1l2."""

import subprocess
import sys
from pathlib import Path

import pytest

_YAML_FEATURE_FLOW = """\
flow: feature-development-flow
version: "1.0"
states:
  - id: planning
    next:
      start:
        to: architecture
  - id: architecture
    next:
      design:
        to: step-2-design
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


@pytest.mark.skip(reason="not yet implemented")
def test_session_management_a1b2c3d4(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/feature-development-flow.yaml
    When the user runs flowr session init feature-development-flow
    Then the CLI creates a session file with the flow name, the initial state, and a default name
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_session_management_i9j0k1l2(tmp_path: Path) -> None:
    """
    Given a session named default already exists
    When the user runs flowr session init feature-development-flow
    Then the CLI prints an error indicating the session already exists
    """
    raise NotImplementedError