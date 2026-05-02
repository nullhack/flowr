"""Tests for session-management-extended feature @ids.

e7f8g9h0 — session-aware next
i1j2k3l4 — session-aware check
q7r8s9t0_list — session list
m3n4o5p6_json — session show with JSON format
e5f6g7h8 — session init with explicit name
g3h4i5j6 — session set-state fails if state not in flow
y5z6a7b8_err — session show fails if session not found
k7l8m9n0_err — session set-state fails if session not found
m5n6o7p8 — session uses config default sessions_dir
q9r0s1t2 — session init resolves flow name from config
"""

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
      start: architecture
  - id: architecture
    next:
      design: done
  - id: done
"""


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        [sys.executable, "-m", "flowr", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def _write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _write_pyproject(
    path: Path, flows_dir: str = ".flowr/flows", sessions_dir: str = ".flowr/sessions"
) -> None:
    content = f"""\
[project]
name = "test-project"
version = "0.1.0"

[tool.flowr]
flows_dir = "{flows_dir}"
sessions_dir = "{sessions_dir}"
default_flow = "main-flow"
default_session = "default"
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_session_management_e7f8g9h0(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr next --session
    Then the CLI reads the flow and state from the session
    and shows available transitions.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    _write_yaml(flows_dir / "feature-development-flow.yaml", _YAML_FEATURE_FLOW)

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

    result = _run_cli("next", "--session", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "architecture" in result.stdout


def test_session_management_i1j2k3l4(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr check --session
    Then the CLI reads the flow and state from the session
    and shows state details.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    _write_yaml(flows_dir / "feature-development-flow.yaml", _YAML_FEATURE_FLOW)

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

    result = _run_cli("check", "--session", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "planning" in result.stdout


def test_session_management_q7r8s9t0_list(tmp_path: Path) -> None:
    """
    Given sessions named default and my-session exist in the session store
    When the user runs flowr session list
    Then the CLI displays all sessions with name, flow, state, and updated_at.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)

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
    (sessions_dir / "my-session.yaml").write_text(
        yaml.dump(
            {
                "flow": "main-flow",
                "state": "discovery",
                "name": "my-session",
                "created_at": "2026-05-01T11:00:00",
                "updated_at": "2026-05-01T11:30:00",
                "stack": [],
                "params": {},
            }
        )
    )

    result = _run_cli("session", "list", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "default" in result.stdout
    assert "my-session" in result.stdout


def test_session_management_m3n4o5p6_json(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr session show --format json
    Then the CLI displays the session state as JSON.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)

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

    result = _run_cli("session", "show", "--format", "json", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr
    import json

    data = json.loads(result.stdout)
    assert data["flow"] == "feature-development-flow"
    assert data["state"] == "planning"


def test_session_management_e5f6g7h8(tmp_path: Path) -> None:
    """
    Given a flow YAML at .flowr/flows/feature-development-flow.yaml
    When the user runs flowr session init feature-development-flow --name my-session
    Then the CLI creates a session file named my-session.yaml.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    _write_yaml(flows_dir / "feature-development-flow.yaml", _YAML_FEATURE_FLOW)

    sessions_dir = tmp_path / ".flowr" / "sessions"
    sessions_dir.mkdir(parents=True)

    result = _run_cli(
        "session",
        "init",
        "feature-development-flow",
        "--name",
        "my-session",
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, result.stderr

    session_file = sessions_dir / "my-session.yaml"
    assert session_file.exists()
    data = yaml.safe_load(session_file.read_text())
    assert data["name"] == "my-session"


def test_session_management_g3h4i5j6(tmp_path: Path) -> None:
    """
    Given a session at feature-development-flow/planning
    When the user runs flowr session set-state nonexistent-state
    Then the CLI prints an error indicating the state is not in the flow.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    _write_yaml(flows_dir / "feature-development-flow.yaml", _YAML_FEATURE_FLOW)

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

    result = _run_cli("session", "set-state", "nonexistent-state", cwd=str(tmp_path))
    assert result.returncode == 1, result.stderr
    assert "not found in flow" in result.stderr


def test_session_management_y5z6a7b8_err(tmp_path: Path) -> None:
    """
    Given no session named nonexistent
    When the user runs flowr session show --name nonexistent
    Then the CLI prints an error indicating the session was not found.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)

    sessions_dir = tmp_path / ".flowr" / "sessions"
    sessions_dir.mkdir(parents=True)

    result = _run_cli("session", "show", "--name", "nonexistent", cwd=str(tmp_path))
    assert result.returncode == 1, result.stderr
    assert "not found" in result.stderr


def test_session_management_k7l8m9n0_err(tmp_path: Path) -> None:
    """
    Given no session named nonexistent
    When the user runs flowr session set-state planning --name nonexistent
    Then the CLI prints an error indicating the session was not found.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)

    sessions_dir = tmp_path / ".flowr" / "sessions"
    sessions_dir.mkdir(parents=True)

    result = _run_cli(
        "session",
        "set-state",
        "planning",
        "--name",
        "nonexistent",
        cwd=str(tmp_path),
    )
    assert result.returncode == 1, result.stderr
    assert "not found" in result.stderr


def test_session_management_m5n6o7p8(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with [tool.flowr] sessions_dir = ".flowr/sessions"
    When the user runs flowr session init feature-development-flow
    Then the CLI stores the session in .flowr/sessions/default.yaml.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    _write_yaml(flows_dir / "feature-development-flow.yaml", _YAML_FEATURE_FLOW)
    _write_pyproject(tmp_path / "pyproject.toml")

    result = _run_cli("session", "init", "feature-development-flow", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr

    session_file = tmp_path / ".flowr" / "sessions" / "default.yaml"
    assert session_file.exists()
    data = yaml.safe_load(session_file.read_text())
    assert data["flow"] == "feature-development-flow"


def test_session_management_q9r0s1t2(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with [tool.flowr] flows_dir = ".flowr/flows"
    When the user runs flowr session init feature-development-flow
    Then the CLI resolves the flow name to .flowr/flows/feature-development-flow.yaml
    before creating the session.
    """
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True)
    _write_yaml(flows_dir / "feature-development-flow.yaml", _YAML_FEATURE_FLOW)
    _write_pyproject(tmp_path / "pyproject.toml")

    result = _run_cli("session", "init", "feature-development-flow", cwd=str(tmp_path))
    assert result.returncode == 0, result.stderr

    session_file = tmp_path / ".flowr" / "sessions" / "default.yaml"
    assert session_file.exists()
    data = yaml.safe_load(session_file.read_text())
    assert data["flow"] == "feature-development-flow"
    assert data["state"] == "planning"
