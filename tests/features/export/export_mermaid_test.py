import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from flowr.__main__ import main

_SIMPLE_YAML = (
    "flow: test\nversion: '1.0'\nexits:\n  - exit_done\n"
    "states:\n  - id: idle\n    next:\n"
    "      go:\n        to: done\n"
    "  - id: done\n    next: {}\n"
)

_GUARDED_YAML = (
    "flow: guarded\nversion: '1.0'\nexits:\n  - exit_done\n"
    "states:\n  - id: idle\n    next:\n"
    "      go:\n        to: done\n        when:\n          score: '>=80'\n"
    "  - id: done\n    next: {}\n"
)


def test_export_mermaid_a2045d96(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format mermaid examples/simple.yaml`
    Then the output is a valid Mermaid stateDiagram-v2 string identical to the previous `flowr mermaid` output
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(_SIMPLE_YAML)

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "mermaid", str(flow_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "stateDiagram-v2" in captured.out
    assert "idle" in captured.out
    assert "done" in captured.out


def test_export_mermaid_67b1b50c(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition with guarded transitions
    When the user runs `flowr export --format mermaid --no-conditions examples/simple.yaml`
    Then the output is a valid stateDiagram-v2 without condition labels on transition edges
    """
    flow_file = tmp_path / "guarded.yaml"
    flow_file.write_text(_GUARDED_YAML)

    with patch.object(
        sys,
        "argv",
        ["flowr", "export", "--format", "mermaid", "--no-conditions", str(flow_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "stateDiagram-v2" in captured.out
    assert "score" not in captured.out


def test_export_mermaid_2e068a23(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a directory `flows/` contains `alpha.yaml` and `beta.yaml`
    When the user runs `flowr export --format mermaid flows/`
    Then the output contains a stateDiagram-v2 for each flow separated by `---`
    """
    flows_dir = tmp_path / "flows"
    flows_dir.mkdir()
    (flows_dir / "beta.yaml").write_text(
        "flow: beta\nversion: '1.0'\nexits:\n  - exit_done\nstates:\n  - id: idle\n    next:\n      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    (flows_dir / "alpha.yaml").write_text(
        "flow: alpha\nversion: '1.0'\nexits:\n  - exit_done\nstates:\n  - id: idle\n    next:\n      go:\n        to: done\n  - id: done\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "mermaid", str(flows_dir)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert captured.out.count("stateDiagram-v2") == 2
    assert "---" in captured.out


def test_export_mermaid_1d5ba172(capsys: pytest.CaptureFixture[str]) -> None:
    """
    When the user runs `flowr export --format json --help`
    Then the help text includes `--flat` and `--no-attrs` options
    """
    with patch.object(sys, "argv", ["flowr", "export", "--format", "json", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "--flat" in captured.out
    assert "--no-attrs" in captured.out


def test_export_mermaid_0ce7099f(capsys: pytest.CaptureFixture[str]) -> None:
    """
    When the user runs `flowr export --format mermaid --help`
    Then the help text includes `--no-conditions` option
    """
    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "mermaid", "--help"]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "--no-conditions" in captured.out
