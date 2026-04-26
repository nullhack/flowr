"""Tests for version output story."""

import importlib.metadata
import subprocess
import sys


def test_cli_entrypoint_c9d0e1f2() -> None:
    """
    Given: the flowrlication package is installed
    When: the user runs `python -m flowr --version`
    Then: the output contains "flowr"
    And: the output contains the version string from package metadata
    And: the process exits with code 0
    """
    version = importlib.metadata.version("flowr")
    result = subprocess.run(
        [sys.executable, "-m", "flowr", "--version"],
        capture_output=True,
        text=True,
    )
    assert "flowr" in result.stdout
    assert version in result.stdout
    assert result.returncode == 0


def test_cli_entrypoint_a3b4c5d6() -> None:
    """
    Given: the flowrlication package is installed
    When: the user runs `python -m flowr --version`
    Then: the version in the output matches `importlib.metadata.version("flowr")`
    """
    version = importlib.metadata.version("flowr")
    result = subprocess.run(
        [sys.executable, "-m", "flowr", "--version"],
        capture_output=True,
        text=True,
    )
    assert version in result.stdout
