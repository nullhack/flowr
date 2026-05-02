"""Configuration resolution for flowr CLI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover
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


_CONFIG_DEFAULTS: dict[str, Any] = {
    "flows_dir": Path(".flowr/flows"),
    "sessions_dir": Path(".flowr/sessions"),
    "default_flow": "main-flow",
    "default_session": "default",
}

_CONFIG_KEYS = ["flows_dir", "sessions_dir", "default_flow", "default_session"]


def _read_pyproject(root: Path) -> dict[str, Any]:
    """Read [tool.flowr] values from pyproject.toml.

    Returns:
        Dict of config values found in pyproject.toml.

    Raises:
        ConfigError: If pyproject.toml exists but is malformed.
    """
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return {}

    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
    except (  # pragma: no cover — rare error path
        tomllib.TOMLDecodeError,
        OSError,
    ) as exc:
        raise ConfigError(f"Failed to read {pyproject_path}: {exc}") from exc

    tool_flowr = data.get("tool", {}).get("flowr", {})
    file_values: dict[str, Any] = {}
    if "flows_dir" in tool_flowr:
        file_values["flows_dir"] = Path(tool_flowr["flows_dir"])
    if "sessions_dir" in tool_flowr:
        file_values["sessions_dir"] = Path(tool_flowr["sessions_dir"])
    if "default_flow" in tool_flowr:
        file_values["default_flow"] = tool_flowr["default_flow"]
    if "default_session" in tool_flowr:
        file_values["default_session"] = tool_flowr["default_session"]
    return file_values


def _resolve_values(
    file_values: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, Any]:
    """Resolve config values with CLI > pyproject.toml > defaults priority."""
    resolved: dict[str, Any] = {}
    for key in _CONFIG_KEYS:
        resolved[key] = overrides.get(key, file_values.get(key, _CONFIG_DEFAULTS[key]))
    return resolved


def _resolve_sources(
    file_values: dict[str, Any],
    overrides: dict[str, Any],
) -> dict[str, str]:
    """Determine the source of each config value."""
    sources: dict[str, str] = {}
    for key in _CONFIG_KEYS:
        if key in overrides:
            sources[key] = "cli"
        elif key in file_values:
            sources[key] = "pyproject.toml"
        else:
            sources[key] = "default"
    sources["project_root"] = "cwd"
    return sources


def _to_config(resolved: dict[str, Any], root: Path) -> FlowrConfig:
    """Convert resolved values dict to a FlowrConfig instance."""
    flows_dir = resolved["flows_dir"]
    sessions_dir = resolved["sessions_dir"]
    if isinstance(flows_dir, str):  # pragma: no cover
        flows_dir = Path(flows_dir)
    if isinstance(sessions_dir, str):  # pragma: no cover
        sessions_dir = Path(sessions_dir)
    return FlowrConfig(
        flows_dir=flows_dir,
        sessions_dir=sessions_dir,
        default_flow=resolved["default_flow"],
        default_session=resolved["default_session"],
        project_root=root,
    )


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
    file_values = _read_pyproject(root)
    resolved = _resolve_values(file_values, overrides)
    return _to_config(resolved, root)


def resolve_config_with_sources(
    project_root: Path | None = None,
    cli_overrides: dict[str, Any] | None = None,
) -> tuple[FlowrConfig, dict[str, str]]:
    """Resolve flowr configuration and track the source of each value.

    Returns:
        Tuple of (FlowrConfig, sources_dict) where sources_dict maps
        each key to "cli", "pyproject.toml", or "default".

    Raises:
        ConfigError: If pyproject.toml exists but [tool.flowr] is malformed.
    """
    root = project_root or Path.cwd()
    overrides = cli_overrides or {}
    file_values = _read_pyproject(root)
    resolved = _resolve_values(file_values, overrides)
    sources = _resolve_sources(file_values, overrides)
    config = _to_config(resolved, root)
    return config, sources
