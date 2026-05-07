import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from flowr.__main__ import main
from flowr.exporters.json_exporter import JsonExporter
from flowr.exporters.mermaid_exporter import MermaidExporter


def test_export_invalid_yaml(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("states:\n  - id: idle\n")

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(bad_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "invalid flow definition" in captured.err


def test_json_adapter_methods() -> None:
    adapter = JsonExporter()
    assert adapter.format_name() == "json"
    assert adapter.description() == "Export flow definitions as JSON"
    assert adapter.supports_directory() is True


def test_mermaid_adapter_methods() -> None:
    adapter = MermaidExporter()
    assert adapter.format_name() == "mermaid"
    assert adapter.description() == "Export flow definitions as Mermaid diagrams"
    assert adapter.supports_directory() is True


def test_json_conditions_serialization(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    flow_file = tmp_path / "guarded.yaml"
    flow_file.write_text(
        "flow: guarded\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: review\n    next:\n"
        "      approve:\n        to: done\n        when:\n          score: '>=80'\n  - id: done\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flow_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    conditioned_edges = [e for e in data["edges"] if "conditions" in e]
    assert len(conditioned_edges) == 1
    assert conditioned_edges[0]["conditions"] == {"score": ">=80"}


def test_json_nonflat_subflow_state_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "main.yaml").write_text(
        "flow: main\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    attrs:\n      owner: SE\n    next:\n"
        "      go:\n        to: sub\n  - id: sub\n    flow: child\n    next:\n      exit_child_done: done\n  - id: done\n    next: {}\n"
    )

    with patch.object(
        sys,
        "argv",
        ["flowr", "export", "--format", "json", str(tmp_path / "main.yaml")],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    idle_node = next(n for n in data["nodes"] if n["id"] == "idle")
    assert idle_node["attrs"] == {"owner": "SE"}
    subflow_nodes = [n for n in data["nodes"] if n["type"] == "subflow"]
    assert len(subflow_nodes) == 1
    assert "attrs" not in subflow_nodes[0]


def test_json_flat_with_attrs_and_conditions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "main.yaml").write_text(
        "flow: main\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: sub\n  - id: sub\n    flow: child\n    next:\n      exit_child_done: done\n  - id: done\n    next: {}\n"
    )
    (tmp_path / "child.yaml").write_text(
        "flow: child\nversion: '1.0'\nexits:\n  - child_done\n"
        "states:\n  - id: start\n    attrs:\n      role: SA\n    next:\n"
        "      run:\n        to: finish\n        when:\n          score: '>=80'\n  - id: finish\n    next: {}\n"
    )

    with patch.object(
        sys,
        "argv",
        ["flowr", "export", "--format", "json", "--flat", str(tmp_path / "main.yaml")],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["flat"] is True
    start_node = next(n for n in data["nodes"] if n["id"] == "sub::start")
    assert start_node["attrs"] == {"role": "SA"}
    conditioned_edges = [e for e in data["edges"] if "conditions" in e]
    assert len(conditioned_edges) == 1
    assert conditioned_edges[0]["conditions"] == {"score": ">=80"}


def test_json_export_directory_single(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    flows_dir = tmp_path / "flows"
    flows_dir.mkdir()
    (flows_dir / "a.yaml").write_text(
        "flow: a\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n      go:\n        to: done\n  - id: done\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flows_dir)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)
    assert data["defaultFlow"] == "a"
    flows = data["flows"]
    assert len(flows) == 1
    assert flows[0]["flow"] == "a"
