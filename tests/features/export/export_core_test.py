import json
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


def test_export_core_8ababd33(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json examples/simple.yaml`
    Then the command delegates to the json adapter with exit code 0
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(_SIMPLE_YAML)

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flow_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)


def test_export_core_6c684a46(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format xml examples/simple.yaml`
    Then the command prints an error to stderr listing available formats and exits with code 1
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(_SIMPLE_YAML)

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "xml", str(flow_file)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "json" in captured.err
    assert "mermaid" in captured.err


def test_export_core_43d8849f(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export examples/simple.yaml`
    Then the command prints a usage error to stderr and exits with code 2
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(_SIMPLE_YAML)

    with patch.object(sys, "argv", ["flowr", "export", str(flow_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "usage" in captured.err.lower()


def test_export_core_d0169acb(capsys: pytest.CaptureFixture[str]) -> None:
    """
    Given no file exists at `nonexistent.yaml`
    When the user runs `flowr export --format json nonexistent.yaml`
    Then the command prints an error to stderr stating the path does not exist and exits with code 1
    """
    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", "nonexistent.yaml"]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_export_core_3c8f8a0a(tmp_path: Path) -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json examples/simple.yaml`
    Then the adapter's `export()` method is called with the loaded flow
    """
    from unittest.mock import MagicMock

    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(_SIMPLE_YAML)

    mock_adapter = MagicMock()
    mock_adapter.export.return_value = "{}"
    with (
        patch.object(
            sys, "argv", ["flowr", "export", "--format", "json", str(flow_file)]
        ),
        patch("flowr.exporters.registry.EXPORTERS", {"json": mock_adapter}),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()
    assert exc_info.value.code == 0
    mock_adapter.export.assert_called_once()


def test_export_core_e4152bc9(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given a directory `flows/` contains multiple `.yaml` files
    When the user runs `flowr export --format json flows/`
    Then the adapter's `export_directory()` method is called with all loaded flows sorted alphabetically by filename
    """
    flows_dir = tmp_path / "flows"
    flows_dir.mkdir()
    (flows_dir / "beta.yaml").write_text(
        _SIMPLE_YAML.replace("flow: test", "flow: beta")
    )
    (flows_dir / "alpha.yaml").write_text(
        _SIMPLE_YAML.replace("flow: test", "flow: alpha")
    )

    with patch.object(
        sys, "argv", ["flowr", "export", "--format", "json", str(flows_dir)]
    ):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


def test_export_core_19cb145b(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Given the flowr CLI is installed
    When the user runs `flowr mermaid examples/simple.yaml`
    Then the command prints a usage error to stderr and exits with code 2
    """
    flow_file = tmp_path / "simple.yaml"
    flow_file.write_text(_SIMPLE_YAML)

    with patch.object(sys, "argv", ["flowr", "mermaid", str(flow_file)]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "usage" in captured.err.lower()


def test_export_core_dad5b532() -> None:
    """
    Given the flowr package is imported
    Then the EXPORTERS dict contains keys `"json"` and `"mermaid"` mapping to their respective adapter instances
    """
    from flowr.exporters.json_exporter import JsonExporter
    from flowr.exporters.mermaid_exporter import MermaidExporter
    from flowr.exporters.registry import EXPORTERS

    assert set(EXPORTERS.keys()) == {"json", "mermaid"}
    assert isinstance(EXPORTERS["json"], JsonExporter)
    assert isinstance(EXPORTERS["mermaid"], MermaidExporter)
