import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from flowr.__main__ import main

_ATTRS_YAML = (
    "flow: attrs-test\nversion: '1.0'\nexits:\n  - exit_done\n"
    "states:\n  - id: idle\n    attrs:\n      owner: SE\n    next:\n"
    "      go:\n        to: done\n  - id: done\n    next: {}\n"
)


def test_export_json_f8eb4019(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow `main.yaml` references a subflow via `flow: child`
    When the user runs `flowr export --format json main.yaml`
    Then the output contains separate flow entries for `main` and `child`, and a `defaultFlow` key indicating the root
    """
    flow_file = tmp_path / "main.yaml"
    flow_file.write_text(
        "flow: main\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: sub\n  - id: sub\n    flow: child\n    next: {}\n"
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flow_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "defaultFlow" in data
    assert data["defaultFlow"] == "main"
    node_types = {n["type"] for n in data["nodes"]}
    assert "subflow" in node_types


def test_export_json_7187f2ad(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow `main.yaml` references a subflow via `flow: child`
    When the user runs `flowr export --format json --flat main.yaml`
    Then all subflow states are merged into the root flow's nodes list with prefixed IDs
    """
    (tmp_path / "main.yaml").write_text(
        "flow: main\nversion: '1.0'\nexits:\n  - exit_done\n"
        "states:\n  - id: idle\n    next:\n"
        "      go:\n        to: sub\n  - id: sub\n    flow: child\n    next:\n      exit_child_done: done\n  - id: done\n    next: {}\n"
    )
    (tmp_path / "child.yaml").write_text(
        "flow: child\nversion: '1.0'\nexits:\n  - child_done\n"
        "states:\n  - id: start\n    next:\n"
        "      run:\n        to: finish\n  - id: finish\n    next: {}\n"
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
    assert data.get("flat") is True
    node_ids = [n["id"] for n in data["nodes"]]
    assert "sub::start" in node_ids
    assert "sub::finish" in node_ids
    assert "idle" in node_ids
    assert "done" in node_ids


def test_export_json_f79514e5(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition with states containing `attrs`
    When the user runs `flowr export --format json --no-attrs examples/simple.yaml`
    Then the output JSON omits the `attrs` field from all nodes
    """
    flow_file = tmp_path / "attrs.yaml"
    flow_file.write_text(_ATTRS_YAML)

    with patch.object(
        sys,
        "argv",
        ["flowr", "export", "--format", "json", "--no-attrs", str(flow_file)],
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    for node in data["nodes"]:
        assert "attrs" not in node


def test_export_json_99a274dd(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a directory `flows/` contains `alpha.yaml` and `beta.yaml`
    When the user runs `flowr export --format json flows/`
    Then the output is a JSON array of flow entries sorted alphabetically, with a top-level `defaultFlow` key
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
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["flow"] == "alpha"
    assert data[1]["flow"] == "beta"
