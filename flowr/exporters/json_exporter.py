"""JSON export adapter for flowr."""

import argparse
import json

from flowr.domain.flow_definition import Flow


class JsonExporter:
    """Export adapter that serializes flow definitions as JSON."""

    def format_name(self) -> str:
        """Return the canonical format name."""
        return "json"

    def description(self) -> str:
        """Return a short human-readable description."""
        return "Export flow definitions as JSON"

    def supports_directory(self) -> bool:
        """Return True — JSON adapter supports directory-mode export."""
        return True

    def add_arguments(self, parser: object) -> None:
        """Register JSON-specific CLI flags."""
        p: argparse.ArgumentParser = parser  # type: ignore[assignment]
        p.add_argument("--flat", action="store_true", dest="adapter_flat")
        p.add_argument("--no-attrs", action="store_true", dest="adapter_no_attrs")

    def _build_subflow_edges(
        self,
        node_id: str,
        child_prefix: str,
        child_flow: Flow,
        state: object,
    ) -> list[dict]:
        """Build entry and exit edges for an inlined subflow."""
        from flowr.domain.flow_definition import State

        s: State = state  # type: ignore[assignment]
        edges: list[dict] = []
        for trigger, transition in s.next.items():
            for entry_state in child_flow.states:
                has_incoming = any(
                    t.target == entry_state.id
                    for st in child_flow.states
                    for t in st.next.values()
                )
                if not has_incoming:
                    edges.append(
                        {
                            "from": node_id,
                            "to": f"{child_prefix}{entry_state.id}",
                            "trigger": trigger,
                        }
                    )
            for exit_name in child_flow.exits:
                if transition.target != exit_name:
                    edges.append(
                        {
                            "from": f"{child_prefix}__exit_{exit_name}",
                            "to": transition.target,
                            "trigger": exit_name,
                        }
                    )
        return edges

    def _inline_subflows(
        self,
        flow: Flow,
        subflows: dict[str, Flow],
        prefix: str = "",
    ) -> tuple[list[dict], list[dict], set[str]]:
        """Recursively inline subflow states with prefixed IDs."""
        include_attrs = True
        nodes: list[dict] = []
        edges: list[dict] = []
        exit_ids: set[str] = set()
        for s in flow.states:
            node_id = f"{prefix}{s.id}" if prefix else s.id
            if s.flow and s.flow in subflows:
                child_flow = subflows[s.flow]
                child_prefix = f"{node_id}::"
                child_nodes, child_edges, _child_exits = self._inline_subflows(
                    child_flow, subflows, child_prefix
                )
                nodes.extend(child_nodes)
                edges.extend(child_edges)
                edges.extend(
                    self._build_subflow_edges(node_id, child_prefix, child_flow, s)
                )
            else:
                node: dict = {"id": node_id, "type": "state"}
                if include_attrs and s.attrs:
                    node["attrs"] = s.attrs
                nodes.append(node)
                exit_ids.update(flow.exits)
                for trigger, transition in s.next.items():
                    target_id = (
                        f"{prefix}{transition.target}" if prefix else transition.target
                    )
                    edge: dict = {
                        "from": node_id,
                        "to": target_id,
                        "trigger": trigger,
                    }
                    if transition.conditions:
                        edge["conditions"] = dict(transition.conditions.conditions)
                    edges.append(edge)
        return nodes, edges, exit_ids

    def _flow_to_dict(
        self,
        flow: Flow,
        options: dict,
        subflows: dict[str, Flow] | None = None,
    ) -> dict:
        """Convert a Flow domain object to a JSON-serializable dict."""
        include_attrs = not options.get("no_attrs")
        flat = options.get("flat", False)
        if flat and subflows:
            nodes, edges, _ = self._inline_subflows(flow, subflows)
            result: dict = {
                "flow": flow.flow,
                "nodes": nodes,
                "edges": edges,
                "flat": True,
            }
        else:
            nodes = []
            for s in flow.states:
                node = {
                    "id": s.id,
                    "type": "subflow" if s.flow else "state",
                }
                if include_attrs and s.attrs:
                    node["attrs"] = s.attrs
                nodes.append(node)
            edges = []
            for state in flow.states:
                for trigger, transition in state.next.items():
                    edge: dict = {
                        "from": state.id,
                        "to": transition.target,
                        "trigger": trigger,
                    }
                    if transition.conditions:
                        edge["conditions"] = dict(transition.conditions.conditions)
                    edges.append(edge)
            result = {"flow": flow.flow, "nodes": nodes, "edges": edges}
        return result

    def export(
        self,
        flow: Flow,
        options: dict,
        subflows: dict[str, Flow] | None = None,
    ) -> str:
        """Export a single flow definition as JSON."""
        result = self._flow_to_dict(flow, options, subflows)
        result["defaultFlow"] = flow.flow
        return json.dumps(result)

    def export_directory(self, flows: list[tuple[str, Flow]], options: dict) -> str:
        """Export a collection of flows as a JSON array."""
        entries = []
        for _name, flow in flows:
            entry = self._flow_to_dict(flow, options)
            entries.append(entry)
        return json.dumps(entries)
