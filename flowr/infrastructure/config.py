"""Configuration resolution for flowr CLI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    import tomli as tomllib


@dataclass(frozen=True, slots=True)
class FlowrConfig:
    """Resolved flowr configuration."""

    flows_dir: Path
    sessions_dir: Path
    default_flow: str
    default_session: str
    project_root: Path

    def flows_path(self) -> Path:
        """Return the resolved flows directory as a Path."""
        return self.project_root / self.flows_dir

    def sessions_path(self) -> Path:
        """Return the resolved sessions directory as a Path."""
        return self.project_root / self.sessions_dir


class ConfigError(Exception):
    """Raised when flowr configuration cannot be resolved."""


def resolve_config(
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> FlowrConfig:
    """Resolve flowr configuration from pyproject.toml with CLI overrides.

    Reads [tool.flowr] from pyproject.toml in project_root (or CWD if not
    given). CLI overrides take precedence over pyproject.toml values, which
    take precedence over defaults.

    Args:
        project_root: Root directory containing pyproject.toml. Defaults to CWD.
        cli_overrides: Dict of CLI flag overrides. Supported keys:
            flows_dir, sessions_dir, default_flow, default_session.

    Returns:
        FlowrConfig with resolved values.

    Raises:
        ConfigError: If pyproject.toml exists but [tool.flowr] is malformed.
    """
    root = project_root or Path.cwd()
    overrides = cli_overrides or {}

    defaults = {
        "flows_dir": Path(".flowr/flows"),
        "sessions_dir": Path(".flowr/sessions"),
        "default_flow": "main-flow",
        "default_session": "default",
    }

    pyproject_path = root / "pyproject.toml"
    file_values: dict[str, Any] = {}

    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            tool_flowr = data.get("tool", {}).get("flowr", {})
            if "flows_dir" in tool_flowr:
                file_values["flows_dir"] = Path(tool_flowr["flows_dir"])
            if "sessions_dir" in tool_flowr:
                file_values["sessions_dir"] = Path(tool_flowr["sessions_dir"])
            if "default_flow" in tool_flowr:
                file_values["default_flow"] = tool_flowr["default_flow"]
            if "default_session" in tool_flowr:
                file_values["default_session"] = tool_flowr["default_session"]
        except (tomllib.TOMLDecodeError, OSError) as exc:
            raise ConfigError(f"Failed to read {pyproject_path}: {exc}") from exc

    flows_dir = overrides.get("flows_dir", file_values.get("flows_dir", defaults["flows_dir"]))
    sessions_dir = overrides.get("sessions_dir", file_values.get("sessions_dir", defaults["sessions_dir"]))
    default_flow = overrides.get("default_flow", file_values.get("default_flow", defaults["default_flow"]))
    default_session = overrides.get("default_session", file_values.get("default_session", defaults["default_session"]))

    if isinstance(flows_dir, str):
        flows_dir = Path(flows_dir)
    if isinstance(sessions_dir, str):
        sessions_dir = Path(sessions_dir)

    return FlowrConfig(
        flows_dir=flows_dir,
        sessions_dir=sessions_dir,
        default_flow=default_flow,
        default_session=default_session,
        project_root=root,
    )