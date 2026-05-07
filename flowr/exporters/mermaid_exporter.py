from flowr.domain.flow_definition import Flow


class MermaidExporter:
    def format_name(self) -> str:
        return "mermaid"

    def description(self) -> str:
        raise NotImplementedError

    def supports_directory(self) -> bool:
        return True

    def add_arguments(self, parser: object) -> None:
        raise NotImplementedError

    def export(self, flow: Flow, options: dict) -> str:
        raise NotImplementedError

    def export_directory(self, flows: list[tuple[str, Flow]], options: dict) -> str:
        raise NotImplementedError
