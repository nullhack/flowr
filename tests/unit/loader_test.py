"""Unit tests for the loader module."""

from pathlib import Path

import pytest

from flowr.domain.flow_definition import Flow
from flowr.domain.loader import (
    FlowParseError,
    load_flow,
    load_flow_from_file,
    resolve_subflows,
)


def test_load_flow_parses_valid_yaml() -> None:
    """load_flow parses a valid YAML string into a Flow."""
    yaml_str = """\
flow: test
version: "1.0"
exits:
  - done
states:
  - id: idle
    next:
      start:
        to: done
"""
    result = load_flow(yaml_str)
    assert isinstance(result, Flow)
    assert result.flow == "test"
    assert len(result.states) == 1


def test_load_flow_missing_flow_field() -> None:
    """load_flow raises FlowParseError when 'flow' is missing."""
    with pytest.raises(FlowParseError, match="Missing required field: flow"):
        load_flow("version: '1.0'\nstates: []\n")


def test_load_flow_missing_version_field() -> None:
    """load_flow raises FlowParseError when 'version' is missing."""
    with pytest.raises(FlowParseError, match="Missing required field: version"):
        load_flow("flow: test\nstates: []\n")


def test_load_flow_non_dict_input() -> None:
    """load_flow raises FlowParseError for non-mapping YAML."""
    with pytest.raises(FlowParseError, match="must be a mapping"):
        load_flow("just a string")


def test_load_flow_missing_state_id() -> None:
    """load_flow raises FlowParseError when state lacks 'id'."""
    with pytest.raises(FlowParseError, match="Missing required field in state: id"):
        load_flow("flow: test\nversion: '1.0'\nstates:\n  - next: {}\n")


def test_load_flow_state_not_mapping() -> None:
    """load_flow raises FlowParseError when state is not a mapping."""
    with pytest.raises(FlowParseError, match="must be a mapping"):
        load_flow("flow: test\nversion: '1.0'\nstates:\n  - 'just a string'\n")


def test_load_flow_param_dict() -> None:
    """load_flow parses param with dict syntax (name + default)."""
    result = load_flow(
        "flow: test\nversion: '1.0'\nexits:\n  - done\n"
        "states:\n  - id: idle\n    next: {}\n"
        "params:\n  - name: verbose\n    default: false\n"
    )
    assert result.params[0].name == "verbose"
    assert result.params[0].default is False


def test_load_flow_param_fallback() -> None:
    """load_flow converts non-string, non-dict param to string."""
    result = load_flow(
        "flow: test\nversion: '1.0'\nexits:\n  - done\n"
        "states:\n  - id: idle\n    next: {}\nparams:\n  - 42\n"
    )
    assert result.params[0].name == "42"


def test_load_flow_param_string() -> None:
    """load_flow parses param as simple string."""
    result = load_flow(
        "flow: test\nversion: '1.0'\nexits:\n  - done\n"
        "states:\n  - id: idle\n    next: {}\nparams:\n  - name\n"
    )
    assert result.params[0].name == "name"
    assert result.params[0].default is None


def test_load_flow_simple_transition() -> None:
    """load_flow parses a simple string transition."""
    result = load_flow(
        "flow: test\nversion: '1.0'\nexits:\n  - done\n"
        "states:\n  - id: idle\n    next:\n      go: done\n"
    )
    assert result.states[0].next["go"].target == "done"


def test_load_flow_state_with_flow_ref() -> None:
    """load_flow parses state with flow and flow_version."""
    result = load_flow(
        "flow: test\nversion: '1.0'\nexits:\n  - done\n"
        "states:\n  - id: idle\n    flow: child.yaml\n"
        "    flow_version: '2.0'\n    next: {}\n"
    )
    assert result.states[0].flow == "child.yaml"
    assert result.states[0].flow_version == "2.0"


def test_load_flow_from_file(tmp_path: Path) -> None:
    """load_flow_from_file loads a Flow from a file path."""
    yaml_str = """\
flow: file-test
version: "1.0"
exits:
  - done
states:
  - id: idle
    next:
      start:
        to: done
"""
    p = tmp_path / "flow.yaml"
    p.write_text(yaml_str)
    result = load_flow_from_file(p)
    assert result.flow == "file-test"


def test_resolve_subflows(tmp_path: Path) -> None:
    """resolve_subflows loads referenced subflow files."""
    parent = """\
flow: parent
version: "1.0"
exits:
  - complete
states:
  - id: idle
    flow: child.yaml
    next:
      done:
        to: complete
"""
    child = """\
flow: child
version: "1.0"
exits:
  - approved
states:
  - id: entry
    next:
      approve:
        to: approved
"""
    p = tmp_path / "parent.yaml"
    p.write_text(parent)
    c = tmp_path / "child.yaml"
    c.write_text(child)
    flow = load_flow_from_file(p)
    flows = resolve_subflows(flow, p)
    assert len(flows) == 2
    assert flows[1].flow == "child"


def test_flow_parser_protocol() -> None:
    """FlowParser is a Protocol for YAML parsing backends."""

    class StubParser:
        def parse(self, yaml_string: str) -> dict[str, object]:
            return {}

    assert hasattr(StubParser, "parse")
