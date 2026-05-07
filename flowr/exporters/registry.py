"""Hardcoded export adapter registry."""

from flowr.domain.export import FlowExporter
from flowr.exporters.json_exporter import JsonExporter
from flowr.exporters.mermaid_exporter import MermaidExporter

EXPORTERS: dict[str, FlowExporter] = {
    "json": JsonExporter(),
    "mermaid": MermaidExporter(),
}
