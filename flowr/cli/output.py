"""Output formatting for CLI results."""

import json
from typing import Any


def format_text(result: dict[str, Any]) -> str:
    """Format a result dict as human-readable key-value text."""
    lines: list[str] = []
    for key, value in result.items():
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
    return "\n".join(lines)


def format_json(result: Any) -> str:  # noqa: ANN401
    """Format a result as JSON."""
    return json.dumps(result, indent=2)
