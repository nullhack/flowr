"""Export adapter protocol for flow definition serialization."""

from typing import Protocol

from flowr.domain.flow_definition import Flow


class FlowExporter(Protocol):
    """Protocol defining the contract for flow export adapters."""

    def format_name(self) -> str:  # pragma: no cover
        """Return the canonical format name (e.g. 'json', 'mermaid')."""
        ...

    def description(self) -> str:  # pragma: no cover
        """Return a short human-readable description of the format."""
        ...

    def supports_directory(self) -> bool:  # pragma: no cover
        """Return True if the adapter supports directory-mode export."""
        ...

    def accepted_options(self) -> list[str]:  # pragma: no cover
        """Return the option keys this adapter consumes."""
        ...

    def add_arguments(self, parser: object) -> None:  # pragma: no cover
        """Register adapter-specific CLI flags on the argparse parser."""
        ...

    def export(
        self,
        flow: Flow,
        options: dict,
        subflows: dict[str, Flow] | None = None,
    ) -> str:  # pragma: no cover
        """Export a single flow definition to the target format."""
        ...

    def export_directory(
        self, flows: list[tuple[str, Flow]], options: dict
    ) -> str:  # pragma: no cover
        """Export a collection of flows to the target format."""
        ...
