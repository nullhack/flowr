"""Mermaid export adapter for flowr."""

import argparse

from flowr.domain.flow_definition import Flow
from flowr.domain.mermaid import to_mermaid


class MermaidExporter:
    """Export adapter that serializes flow definitions as Mermaid diagrams."""

    def format_name(self) -> str:
        """Return the canonical format name."""
        return "mermaid"

    def description(self) -> str:
        """Return a short human-readable description."""
        return "Export flow definitions as Mermaid diagrams"

    def supports_directory(self) -> bool:
        """Return True — Mermaid adapter supports directory-mode export."""
        return True

    def accepted_options(self) -> list[str]:
        """Return the option keys the Mermaid adapter consumes."""
        return ["no_conditions"]

    def add_arguments(self, parser: object) -> None:
        """Register Mermaid-specific CLI flags."""
        p: argparse.ArgumentParser = parser  # type: ignore[assignment]
        p.add_argument(
            "--no-conditions",
            action="store_true",
            dest="adapter_no_conditions",
        )

    def export(
        self,
        flow: Flow,
        options: dict,
        subflows: dict[str, Flow] | None = None,
    ) -> str:
        """Export a single flow definition as a Mermaid stateDiagram-v2."""
        diagram = to_mermaid(flow)
        if options.get("no_conditions"):
            lines = diagram.split("\n")
            filtered = [lines[0]]
            for line in lines[1:]:
                if " --> " in line and " : " in line:
                    parts = line.split(" : ", 1)
                    trigger_part = parts[1].split(" | ")[0]
                    filtered.append(f"{parts[0]} : {trigger_part}")
                else:
                    filtered.append(line)
            diagram = "\n".join(filtered)
        return diagram

    def export_directory(self, flows: list[tuple[str, Flow]], options: dict) -> str:
        """Export a collection of flows as separated Mermaid diagrams."""
        diagrams = []
        for _name, flow in flows:
            diagrams.append(self.export(flow, options))
        return "\n---\n".join(diagrams)
