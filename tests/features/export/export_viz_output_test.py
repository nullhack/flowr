import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from flowr.__main__ import main


def test_export_viz_output_a7b9c1d3(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json --output /tmp/flowr-out.json examples/simple.yaml`
    Then the file `/tmp/flowr-out.json` contains valid JSON output and nothing is printed to stdout
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(
        "flow: test-flow\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    output_file = tmp_path / "flowr-out.json"

    with patch.object(
        sys,
        "argv",
        [
            "flowr",
            "export",
            "--format",
            "json",
            "--output",
            str(output_file),
            str(flow_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert captured.out == ""
    data = json.loads(output_file.read_text())
    assert data["flow"] == "test-flow"


def test_export_viz_output_b8c0d2e4(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json --output /tmp/flowr/deep/nested/out.json examples/simple.yaml`
    Then the parent directories `/tmp/flowr/deep/nested/` are created and the file is written successfully
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(
        "flow: test-flow\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    output_file = tmp_path / "deep" / "nested" / "out.json"

    with patch.object(
        sys,
        "argv",
        [
            "flowr",
            "export",
            "--format",
            "json",
            "--output",
            str(output_file),
            str(flow_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    assert output_file.exists()
    data = json.loads(output_file.read_text())
    assert data["flow"] == "test-flow"


def test_export_viz_output_c9d1e3f5(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format mermaid --output /tmp/flowr-out.mmd examples/simple.yaml`
    Then the file `/tmp/flowr-out.mmd` contains valid Mermaid stateDiagram-v2 output
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(
        "flow: test-flow\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    output_file = tmp_path / "flowr-out.mmd"

    with patch.object(
        sys,
        "argv",
        [
            "flowr",
            "export",
            "--format",
            "mermaid",
            "--output",
            str(output_file),
            str(flow_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    content = output_file.read_text()
    assert "stateDiagram-v2" in content


def test_export_viz_output_d0e2f4a6(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    r"""
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json --output .flowr/viz/data.js examples/simple.yaml`
    Then the file content starts with `window.FLOWVIZ_DATA = ` followed by the JSON object and ending with `;\n`
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(
        "flow: test-flow\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    output_file = tmp_path / "data.js"

    with patch.object(
        sys,
        "argv",
        [
            "flowr",
            "export",
            "--format",
            "json",
            "--output",
            str(output_file),
            str(flow_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    content = output_file.read_text()
    assert content.startswith("window.FLOWVIZ_DATA = ")
    assert content.endswith(";\n")
    json_part = content[len("window.FLOWVIZ_DATA = ") : -2]
    data = json.loads(json_part)
    assert data["flow"] == "test-flow"


def test_export_viz_output_e1f3a5b7(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format mermaid --output /tmp/out.js examples/simple.yaml`
    Then the file contains plain Mermaid output without `window.FLOWVIZ_DATA` wrapping
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(
        "flow: test-flow\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    output_file = tmp_path / "out.js"

    with patch.object(
        sys,
        "argv",
        [
            "flowr",
            "export",
            "--format",
            "mermaid",
            "--output",
            str(output_file),
            str(flow_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    content = output_file.read_text()
    assert "window.FLOWVIZ_DATA" not in content
    assert "stateDiagram-v2" in content


def test_export_viz_output_f2a4b6c8(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json --output /tmp/out.json examples/simple.yaml`
    Then the file contains raw JSON without any JavaScript wrapping
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(
        "flow: test-flow\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    output_file = tmp_path / "out.json"

    with patch.object(
        sys,
        "argv",
        [
            "flowr",
            "export",
            "--format",
            "json",
            "--output",
            str(output_file),
            str(flow_file),
        ],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    content = output_file.read_text()
    assert not content.startswith("window.FLOWVIZ_DATA")
    data = json.loads(content)
    assert data["flow"] == "test-flow"
