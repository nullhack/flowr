"""Flow name resolution: maps short flow names to file paths.

If the argument is an existing file path, return it directly.
Otherwise, treat it as a flow name and search the configured
flows directory for a matching .yaml file.
"""

from pathlib import Path
from typing import Protocol


class FlowNameNotFoundError(Exception):
    """Raised when a flow name cannot be resolved to a file path."""

    def __init__(self, flow_name: str, flows_dir: Path) -> None:
        """Initialize with the unresolvable flow name and searched directory."""
        self.flow_name = flow_name
        self.flows_dir = flows_dir
        super().__init__(f"Flow not found: '{flow_name}' (searched in {flows_dir})")


class FlowNameResolver(Protocol):
    """Resolve a flow name or file path to a valid flow file path.

    If the argument is an existing file path, return it directly.
    Otherwise, treat it as a flow name and search the configured
    flows directory for a matching .yaml file.
    """

    def resolve(self, flow_arg: str, flows_dir: Path) -> Path:  # pragma: no cover
        """Resolve a flow argument to a file path.

        Args:
            flow_arg: A file path or short flow name.
            flows_dir: The configured flows directory.

        Returns:
            The resolved Path to the flow YAML file.

        Raises:
            FlowNameNotFoundError: The argument is not an existing file
                and no matching .yaml file exists in flows_dir.
        """
        ...


class DefaultFlowNameResolver:
    """Default implementation: file paths first, then name resolution."""

    def resolve(self, flow_arg: str, flows_dir: Path) -> Path:
        """Resolve a flow argument to a file path.

        If flow_arg is an existing file path, return it directly
        (backward compatible). Otherwise, treat it as a flow name
        and look for {flows_dir}/{flow_name}.yaml.

        Args:
            flow_arg: A file path or short flow name.
            flows_dir: The configured flows directory.

        Returns:
            The resolved Path to the flow YAML file.

        Raises:
            FlowNameNotFoundError: The argument is not an existing file
                and no matching .yaml file exists in flows_dir.
        """
        path = Path(flow_arg)
        if path.exists():
            return path

        name = flow_arg
        if not name.endswith(".yaml"):
            name = f"{name}.yaml"

        resolved = flows_dir / name
        if resolved.exists():
            return resolved

        raise FlowNameNotFoundError(flow_arg, flows_dir)
