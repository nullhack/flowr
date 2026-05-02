"""Tests for config introspection rule — @id tags 2e301322, 36d41122, 9d4c4973."""

import subprocess
import sys
from pathlib import Path


def _write_pyproject(tmp_path: Path, flows_dir: str | None = None) -> Path:
    if flows_dir is not None:
        content = f'[tool.flowr]\nflows_dir = "{flows_dir}"\n'
    else:
        content = ""
    p = tmp_path / "pyproject.toml"
    p.write_text(content)
    return p


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-m", "flowr", *args]
    return subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_configurable_paths_2e301322(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with [tool.flowr] flows_dir = "src/flows"
    When the user runs flowr config
    Then the output shows flows_dir = src/flows with source pyproject.toml
    """
    _write_pyproject(tmp_path, flows_dir="src/flows")
    result = _run_cli("config", cwd=str(tmp_path))
    assert result.returncode == 0
    assert "src/flows" in result.stdout
    assert "pyproject.toml" in result.stdout


def test_configurable_paths_36d41122(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with no [tool.flowr] section
    When the user runs flowr config
    Then the output shows flows_dir with its default value and source default
    """
    _write_pyproject(tmp_path, flows_dir=None)
    result = _run_cli("config", cwd=str(tmp_path))
    assert result.returncode == 0
    assert "default" in result.stdout


def test_configurable_paths_9d4c4973(tmp_path: Path) -> None:
    """
    Given a pyproject.toml with [tool.flowr] flows_dir = "src/flows"
    When the user runs flowr config --flows-dir other/flows
    Then the output shows flows_dir = other/flows with source cli
    """
    _write_pyproject(tmp_path, flows_dir="src/flows")
    result = _run_cli("--flows-dir", "other/flows", "config", cwd=str(tmp_path))
    assert result.returncode == 0
    assert "other/flows" in result.stdout
    assert "cli" in result.stdout
