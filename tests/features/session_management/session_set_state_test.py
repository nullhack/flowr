"""Tests for session set-state rule — @id tag c9d0e1f2."""

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


@pytest.mark.skip(reason="not yet implemented")
def test_session_management_c9d0e1f2(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr session set-state architecture
    Then the CLI updates the session state to architecture and persists it
    """
    raise NotImplementedError