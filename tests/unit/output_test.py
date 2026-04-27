"""Unit tests for CLI output formatting."""

from flowr.cli.output import format_json, format_text


def test_format_text_simple_key_value() -> None:
    """format_text renders simple key-value pairs."""
    result = format_text({"name": "test", "count": 3})
    assert "name: test" in result
    assert "count: 3" in result


def test_format_text_empty_list() -> None:
    """format_text renders empty lists as (none)."""
    result = format_text({"items": []})
    assert "items: (none)" in result


def test_format_text_string_list() -> None:
    """format_text renders string lists with repeated keys."""
    result = format_text({"states": ["idle", "done"]})
    assert "states: idle" in result
    assert "states: done" in result


def test_format_text_dict_list() -> None:
    """format_text renders dict lists with indented key-values."""
    result = format_text({"violations": [{"severity": "MUST", "message": "err"}]})
    assert "severity: MUST" in result
    assert "message: err" in result


def test_format_text_nested_dict() -> None:
    """format_text renders nested dicts with key-values."""
    result = format_text({"attrs": {"color": "blue", "size": 1}})
    assert "color: blue" in result
    assert "size: 1" in result


def test_format_json_dict() -> None:
    """format_json renders a dict as indented JSON."""
    result = format_json({"valid": True, "count": 2})
    assert '"valid": true' in result
    assert '"count": 2' in result


def test_format_json_list() -> None:
    """format_json renders a list as indented JSON."""
    result = format_json(["idle", "done"])
    assert '"idle"' in result
    assert '"done"' in result
