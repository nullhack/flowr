"""Unit tests for session store edge cases."""

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


def test_set_state_rejects_invalid_state(tmp_path: Path) -> None:
    """Setting a non-existent state should exit with code 1 and report error."""
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

    result = _run_cli("session", "set-state", "nonexistent", cwd=str(tmp_path))
    assert result.returncode == 1
    assert "not found" in result.stderr
