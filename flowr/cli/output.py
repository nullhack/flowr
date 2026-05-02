"""Output formatting for CLI results."""

import json
from typing import Any


def _format_dict_lines(data: dict[str, Any]) -> list[str]:
    """Format a single dict as key-value lines."""
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, list):
            if not value:
                lines.append(f"{key}: (none)")
            elif isinstance(value[0], dict):
                for item in value:
                    for k, v in item.items():
                        lines.append(f"  {k}: {v}")
            else:
                for item in value:
                    lines.append(f"{key}: {item}")
        elif isinstance(value, dict):
            for k, v in value.items():
                lines.append(f"{k}: {v}")
        else:
            lines.append(f"{key}: {value}")
    return lines


def format_text(result: dict[str, Any] | list[dict[str, Any]]) -> str:
    """Format a result dict or list of dicts as human-readable text."""
    if isinstance(result, list):
        lines: list[str] = []
        for item in result:
            lines.extend(_format_dict_lines(item))
            lines.append("---")
        if lines:
            lines.pop()
        return "\n".join(lines)
    return "\n".join(_format_dict_lines(result))


def format_json(result: Any) -> str:  # noqa: ANN401
    """Format a result as JSON."""
    return json.dumps(result, indent=2)
