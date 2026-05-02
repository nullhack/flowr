"""Tests for session set-state rule — @id tag c9d0e1f2."""

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


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "flowr", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_session_management_c9d0e1f2(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr session set-state architecture
    Then the CLI updates the session state to architecture and persists it
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

    result = _run_cli("session", "set-state", "architecture", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr

    session_data = yaml.safe_load((sessions_dir / "default.yaml").read_text())
    assert session_data["state"] == "architecture"
