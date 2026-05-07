import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from flowr.__main__ import main


def test_export_viz_pipeline_a1c3e5f7(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition with version "1.0.20260507" and exits ["done", "failed"]
    When the user runs `flowr export --format json examples/simple.yaml`
    Then the JSON output contains a `version` field matching "1.0.20260507" and an `exits` field matching ["done", "failed"]
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(
        "flow: test-flow\nversion: '1.0.20260507'\nexits:\n  - done\n  - failed\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: finished\n  - id: finished\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flow_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["version"] == "1.0.20260507"
    assert data["exits"] == ["done", "failed"]


def test_export_viz_pipeline_b2d4f6a8(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow where state "drill-down" has `flow: child-flow` and `flow_version: 2.0.0`
    When the user runs `flowr export --format json main.yaml`
    Then the node for "drill-down" includes `"subflow": "child-flow"` and `"subflowVersion": "2.0.0"`
    """
    flow_file = tmp_path / "main.yaml"
    flow_file.write_text(
        "flow: parent\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: drill-down\n  - id: drill-down\n    flow: child-flow\n    flow_version: '2.0.0'\n    next:\n      exit_child_done: done\n  - id: done\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flow_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    drill_down_node = next(n for n in data["nodes"] if n["id"] == "drill-down")
    assert drill_down_node["subflow"] == "child-flow"
    assert drill_down_node["subflowVersion"] == "2.0.0"


def test_export_viz_pipeline_c3e5f7a9(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow with states that have no `flow` field
    When the user runs `flowr export --format json examples/simple.yaml`
    Then no node in the output contains a `subflow` or `subflowVersion` field
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(
        "flow: plain-flow\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: done\n  - id: done\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flow_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for node in data["nodes"]:
        assert "subflow" not in node
        assert "subflowVersion" not in node


def test_export_viz_pipeline_d4f6a8b0(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a directory `flows/` contains `alpha.yaml` and `beta.yaml`
    When the user runs `flowr export --format json flows/`
    Then the output is a JSON object (not array) with a `defaultFlow` key and a `flows` key containing an array of flow entries sorted alphabetically by filename
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
        sys, "argv", ["flowr", "export", "--format", "json", str(flows_dir)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)
    assert "defaultFlow" in data
    assert "flows" in data
    flows = data["flows"]
    assert isinstance(flows, list)
    assert len(flows) == 2
    assert flows[0]["flow"] == "alpha"
    assert flows[1]["flow"] == "beta"


def test_export_viz_pipeline_e5f7a9b1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a directory contains `main-flow.yaml` and `other.yaml`
    When the user runs `flowr export --format json flows/`
    Then the `defaultFlow` value is `"main-flow"`
    """
    flows_dir = tmp_path / "flows"
    flows_dir.mkdir()
    (flows_dir / "main-flow.yaml").write_text(
        "flow: main-flow\nversion: '1.0'\nexits:\n  - exit_done\nstates:\n  - id: idle\n    next:\n      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    (flows_dir / "other.yaml").write_text(
        "flow: other\nversion: '1.0'\nexits:\n  - exit_done\nstates:\n  - id: idle\n    next:\n      go:\n        to: done\n  - id: done\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flows_dir)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["defaultFlow"] == "main-flow"


def test_export_viz_pipeline_f6a8b0c2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a directory contains `beta.yaml` and `gamma.yaml` but no `main-flow.yaml`
    When the user runs `flowr export --format json flows/`
    Then the `defaultFlow` value is `"beta"`
    """
    flows_dir = tmp_path / "flows"
    flows_dir.mkdir()
    (flows_dir / "beta.yaml").write_text(
        "flow: beta\nversion: '1.0'\nexits:\n  - exit_done\nstates:\n  - id: idle\n    next:\n      go:\n        to: done\n  - id: done\n    next: {}\n"
    )
    (flows_dir / "gamma.yaml").write_text(
        "flow: gamma\nversion: '1.0'\nexits:\n  - exit_done\nstates:\n  - id: idle\n    next:\n      go:\n        to: done\n  - id: done\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flows_dir)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["defaultFlow"] == "beta"
