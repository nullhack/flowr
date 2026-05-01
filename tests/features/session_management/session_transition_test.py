"""Tests for session-aware transition rule — @id tags o1p2q3r4, s5t6u7v8, w9x0y1z2."""

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
def test_session_management_o1p2q3r4(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr transition --session architecture
    Then the CLI reads the flow and state from the session, performs the transition, and auto-updates the session
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_session_management_s5t6u7v8(tmp_path: Path) -> None:
    """
    Given a session at feature-development-flow/step-1-scope and the transition enters a subflow
    When the user runs flowr transition --session some-trigger
    Then the CLI pushes the parent flow+state onto the session stack and updates the state to the subflow's initial state
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_session_management_w9x0y1z2(tmp_path: Path) -> None:
    """
    Given a session with a stack frame and the transition exits the subflow
    When the user runs flowr transition --session complete
    Then the CLI pops the stack frame and restores the parent flow+state
    """
    raise NotImplementedError