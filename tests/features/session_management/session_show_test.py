"""Tests for session show rule — @id tags m3n4o5p6 and u1v2w3x4."""

import subprocess
import sys
from pathlib import Path

import yaml


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "flowr", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_session_management_m3n4o5p6(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr session show
    Then the CLI displays the flow, state, stack, and timestamps
    """
    sessions_dir = tmp_path / ".flowr" / "sessions"
    sessions_dir.mkdir(parents=True)
    (sessions_dir / "default.yaml").write_text(
        yaml.dump(
            {
                "flow": "feature-development-flow",
                "state": "planning",
                "name": "default",
                "created_at": "2026-05-01T10:00:00",
                "updated_at": "2026-05-01T14:22:00",
                "stack": [],
                "params": {},
            }
        )
    )

    result = _run_cli("session", "show", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "feature-development-flow" in result.stdout
    assert "planning" in result.stdout
    assert "2026-05-01T10:00:00" in result.stdout
    assert "2026-05-01T14:22:00" in result.stdout


def test_session_management_u1v2w3x4(tmp_path: Path) -> None:
    """
    Given a session with a subflow stack containing one frame
    When the user runs flowr session show
    Then the CLI displays the stack entries showing parent flow and state
    """
    sessions_dir = tmp_path / ".flowr" / "sessions"
    sessions_dir.mkdir(parents=True)
    (sessions_dir / "default.yaml").write_text(
        yaml.dump(
            {
                "flow": "scope-cycle",
                "state": "step-1-scope",
                "name": "default",
                "created_at": "2026-05-01T10:00:00",
                "updated_at": "2026-05-01T14:25:00",
                "stack": [
                    {"flow": "feature-development-flow", "state": "step-1-scope"},
                ],
                "params": {},
            }
        )
    )

    result = _run_cli("session", "show", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "feature-development-flow" in result.stdout
    assert "step-1-scope" in result.stdout
