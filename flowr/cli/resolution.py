"""Flow name resolution: maps short flow names to file paths.

If the argument is an existing file path, return it directly.
Otherwise, treat it as a flow name and search the configured
flows directory for a matching .yaml file.
"""

from pathlib import Path
from typing import Protocol


class FlowNameNotFound(Exception):
    """Raised when a flow name cannot be resolved to a file path."""


class FlowNameResolver(Protocol):
    """Resolve a flow name or file path to a valid flow file path.

    If the argument is an existing file path, return it directly.
    Otherwise, treat it as a flow name and search the configured
    flows directory for a matching .yaml file.
    """

    def resolve(self, flow_arg: str, flows_dir: Path) -> Path:
        """Resolve a flow argument to a file path.

        Args:
            flow_arg: A file path or short flow name.
            flows_dir: The configured flows directory.

        Returns:
            The resolved Path to the flow YAML file.

        Raises:
            FlowNameNotFound: The argument is not an existing file
                and no matching .yaml file exists in flows_dir.
        """
        ...


class DefaultFlowNameResolver:
    """Default implementation: file paths first, then name resolution."""

    def resolve(self, flow_arg: str, flows_dir: Path) -> Path:
        """Resolve a flow argument to a file path.

        Args:
            flow_arg: A file path or short flow name.
            flows_dir: The configured flows directory.

        Returns:
            The resolved Path to the flow YAML file.

        Raises:
            FlowNameNotFound: The argument is not an existing file
                and no matching .yaml file exists in flows_dir.
        """
        raise NotImplementedError