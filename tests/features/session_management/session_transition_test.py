"""Tests for session-aware transition rule — @id tags o1p2q3r4, s5t6u7v8, w9x0y1z2."""

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
  - id: step-2-design
    next:
      complete:
        to: done
  - id: done
"""

_YAML_SUBFLOW = """\
flow: scope-cycle
version: "1.0"
exits:
  - done
states:
  - id: step-1-scope
    next:
      complete:
        to: done
  - id: step-2-design
"""

_YAML_FEATURE_WITH_SUBFLOW = """\
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
        to: step-1-scope
  - id: step-1-scope
    flow: scope-cycle.yaml
    next:
      complete:
        to: done
  - id: done
    next:
      exit-subflow:
        to: step-2-design
  - id: step-2-design
"""


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "flowr", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_session_management_o1p2q3r4(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr transition --session architecture
    Then the CLI reads the flow and state from the session,
    performs the transition, and auto-updates the session
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

    result = _run_cli("transition", "start", "--session", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr

    session_data = yaml.safe_load((sessions_dir / "default.yaml").read_text())
    assert session_data["state"] == "architecture"


def test_session_management_s5t6u7v8(tmp_path: Path) -> None:
    """
    Given a session at feature-development-flow/step-1-scope
    and the transition enters a subflow
    When the user runs flowr transition --session some-trigger
    Then the CLI pushes the parent flow+state onto the session stack
    and updates the state to the subflow's initial state
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    (flows_dir / "feature-development-flow.yaml").write_text(_YAML_FEATURE_WITH_SUBFLOW)
    (flows_dir / "scope-cycle.yaml").write_text(_YAML_SUBFLOW)

    sessions_dir = tmp_path / ".flowr" / "sessions"
    sessions_dir.mkdir(parents=True)
    (sessions_dir / "default.yaml").write_text(
        yaml.dump(
            {
                "flow": "feature-development-flow",
                "state": "architecture",
                "name": "default",
                "created_at": "2026-05-01T10:00:00",
                "updated_at": "2026-05-01T10:00:00",
                "stack": [],
                "params": {},
            }
        )
    )

    result = _run_cli("transition", "design", "--session", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr

    session_data = yaml.safe_load((sessions_dir / "default.yaml").read_text())
    assert session_data["flow"] == "scope-cycle"
    assert session_data["state"] == "step-1-scope"
    assert len(session_data["stack"]) == 1
    assert session_data["stack"][0]["flow"] == "feature-development-flow"
    assert session_data["stack"][0]["state"] == "architecture"


def test_session_management_w9x0y1z2(tmp_path: Path) -> None:
    """
    Given a session with a stack frame and the transition exits the subflow
    When the user runs flowr transition --session complete
    Then the CLI pops the stack frame and restores the parent flow+state
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    (flows_dir / "feature-development-flow.yaml").write_text(_YAML_FEATURE_WITH_SUBFLOW)
    (flows_dir / "scope-cycle.yaml").write_text(_YAML_SUBFLOW)

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
                    {"flow": "feature-development-flow", "state": "architecture"},
                ],
                "params": {},
            }
        )
    )

    result = _run_cli("transition", "complete", "--session", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr

    session_data = yaml.safe_load((sessions_dir / "default.yaml").read_text())
    assert session_data["flow"] == "feature-development-flow"
    assert session_data["state"] == "done"
    assert len(session_data["stack"]) == 0
