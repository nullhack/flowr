"""Tests for session init rule — @id tags a1b2c3d4 and i9j0k1l2."""

import subprocess
import sys
from pathlib import Path

import yaml

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


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "flowr", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_session_management_a1b2c3d4(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/feature-development-flow.yaml
    When the user runs flowr session init feature-development-flow
    Then the CLI creates a session file with the flow name,
    the initial state, and a default name
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    (flows_dir / "feature-development-flow.yaml").write_text(_YAML_FEATURE_FLOW)

    result = _run_cli("session", "init", "feature-development-flow", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr

    sessions_dir = tmp_path / ".flowr" / "sessions"
    session_file = sessions_dir / "default.yaml"
    assert session_file.exists()

    session_data = yaml.safe_load(session_file.read_text())
    assert session_data["flow"] == "feature-development-flow"
    assert session_data["state"] == "planning"
    assert session_data["name"] == "default"


def test_session_management_i9j0k1l2(tmp_path: Path) -> None:
    """
    Given a session named default already exists
    When the user runs flowr session init feature-development-flow
    Then the CLI prints an error indicating the session already exists
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    (flows_dir / "feature-development-flow.yaml").write_text(_YAML_FEATURE_FLOW)

    sessions_dir = tmp_path / ".flowr" / "sessions"
    sessions_dir.mkdir(parents=True)
    (sessions_dir / "default.yaml").write_text(
        yaml.dump(
            {
                "flow": "feature-development-flow",
                "state": "planning",
                "name": "default",
                "created_at": "2026-05-01T10:00:00",
                "updated_at": "2026-05-01T10:00:00",
                "stack": [],
                "params": {},
            }
        )
    )

    result = _run_cli("session", "init", "feature-development-flow", cwd=str(tmp_path))
    assert result.returncode == 1
    assert "already exists" in result.stderr
