"""Tests for session show rule — @id tags m3n4o5p6 and u1v2w3x4."""

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
def test_session_management_m3n4o5p6(tmp_path: Path) -> None:
    """
    Given a session named default at feature-development-flow/planning
    When the user runs flowr session show
    Then the CLI displays the flow, state, stack, and timestamps
    """
    raise NotImplementedError


@pytest.mark.skip(reason="not yet implemented")
def test_session_management_u1v2w3x4(tmp_path: Path) -> None:
    """
    Given a session with a subflow stack containing one frame
    When the user runs flowr session show
    Then the CLI displays the stack entries showing parent flow and state
    """
    raise NotImplementedError