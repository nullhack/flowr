"""Tests for export robustness: unused flags, empty directory, malformed YAML."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from flowr.__main__ import main

_SIMPLE_YAML = """\
flow: test-flow
version: "1.0"
exits: [done]
states:
  - id: start
    next:
      ready: done
  - id: done
"""

_MALFORMED_YAML = "flow: [\n  invalid: {"


def _write_flow(path: Path, content: str = _SIMPLE_YAML) -> Path:
    path.write_text(content)
    return path


def test_export_robustness_a1b2c3d4(capsys, tmp_path):
    """JSON format with --no-conditions flag.

    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json --no-conditions examples/simple.yaml`
    Then the command prints a warning to stderr containing "no-conditions" and exits with code 0
    """
    flow_file = _write_flow(tmp_path / "simple.yaml")
    with (
        patch.object(
            sys,
            "argv",
            ["flowr", "export", "--format", "json", "--no-conditions", str(flow_file)],
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "no-conditions" in captured.err
    data = json.loads(captured.out)
    assert data["flow"] == "test-flow"


def test_export_robustness_e5f6a7b8(capsys, tmp_path):
    """Mermaid format with --flat flag.

    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format mermaid --flat examples/simple.yaml`
    Then the command prints a warning to stderr containing "flat" and exits with code 0
    """
    flow_file = _write_flow(tmp_path / "simple.yaml")
    with (
        patch.object(
            sys,
            "argv",
            ["flowr", "export", "--format", "mermaid", "--flat", str(flow_file)],
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "flat" in captured.err
    assert "stateDiagram-v2" in captured.out


def test_export_robustness_c9d0e1f2(capsys, tmp_path):
    """Export from empty directory.

    Given a directory exists at `/tmp/empty_flows` with no YAML files
    When the user runs `flowr export --format json /tmp/empty_flows`
    Then the command prints an error to stderr stating no flow files were found and exits with code 1
    """
    empty_dir = tmp_path / "empty_flows"
    empty_dir.mkdir()
    with (
        patch.object(
            sys, "argv", ["flowr", "export", "--format", "json", str(empty_dir)]
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "no flow files" in captured.err


def test_export_robustness_a3b4c5d6(capsys, tmp_path):
    """Export from directory with only non-YAML files.

    Given a directory exists at `/tmp/mixed` containing only .txt and .json files
    When the user runs `flowr export --format json /tmp/mixed`
    Then the command prints an error to stderr stating no flow files were found and exits with code 1
    """
    mixed_dir = tmp_path / "mixed"
    mixed_dir.mkdir()
    (mixed_dir / "readme.txt").write_text("not a flow")
    (mixed_dir / "data.json").write_text("{}")
    with (
        patch.object(
            sys, "argv", ["flowr", "export", "--format", "json", str(mixed_dir)]
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "no flow files" in captured.err


def test_export_robustness_e7f8a9b0(capsys, tmp_path):
    """Malformed YAML with export command.

    Given a file at `/tmp/bad.yaml` contains invalid YAML syntax
    When the user runs `flowr export --format json /tmp/bad.yaml`
    Then the command prints a single-line error to stderr with no traceback and exits with code 1
    """
    bad_file = _write_flow(tmp_path / "bad.yaml", _MALFORMED_YAML)
    with (
        patch.object(
            sys, "argv", ["flowr", "export", "--format", "json", str(bad_file)]
        ),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.strip()
    assert "Traceback" not in captured.err
    assert "\n" not in captured.err.strip()


def test_export_robustness_c1d2e3f4(capsys, tmp_path):
    """Malformed YAML with validate command.

    Given a file at `/tmp/bad.yaml` contains invalid YAML syntax
    When the user runs `flowr validate /tmp/bad.yaml`
    Then the command prints a single-line error to stderr with no traceback and exits with code 1
    """
    bad_file = _write_flow(tmp_path / "bad.yaml", _MALFORMED_YAML)
    with (
        patch.object(sys, "argv", ["flowr", "validate", str(bad_file)]),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.strip()
    assert "Traceback" not in captured.err
    assert "\n" not in captured.err.strip()
