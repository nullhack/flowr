"""Unit tests for output.py list-of-dicts formatting."""

from flowr.cli.output import format_json, format_text


class TestFormatTextListOfDicts:
    def test_list_of_dicts(self) -> None:
        data = [
            {"name": "alpha", "flow": "main"},
            {"name": "beta", "flow": "sub"},
        ]
        result = format_text(data)
        assert "name: alpha" in result
        assert "flow: main" in result
        assert "name: beta" in result
        assert "---" in result

    def test_empty_list(self) -> None:
        result = format_text([])
        assert result == ""


class TestFormatJsonListOfDicts:
    def test_list_of_dicts(self) -> None:
        data = [
            {"name": "alpha", "flow": "main"},
            {"name": "beta", "flow": "sub"},
        ]
        result = format_json(data)
        assert '"name": "alpha"' in result
        assert '"name": "beta"' in result
