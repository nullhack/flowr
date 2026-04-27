"""YAML parsing for flow definitions."""

from pathlib import Path
from typing import Any, Protocol

import yaml

from flowr.domain.flow_definition import Flow, GuardCondition, Param, State, Transition


class FlowParseError(Exception):
    """Raised when a flow definition cannot be parsed."""


class FlowParser(Protocol):
    """Protocol for YAML parsing backends."""

    def parse(self, yaml_string: str) -> dict[str, Any]:
        """Parse a YAML string into a dictionary."""
        ...  # pragma: no cover


def load_flow(yaml_string: str, parser: FlowParser | None = None) -> Flow:
    """Parse a YAML document into a Flow domain object."""
    raw: dict[str, Any] = yaml.safe_load(yaml_string)
    return _dict_to_flow(raw)


def load_flow_from_file(path: Path) -> Flow:
    """Load a flow definition from a YAML file."""
    return load_flow(path.read_text(encoding="utf-8"))


def resolve_subflows(root_flow: Flow, root_path: Path) -> list[Flow]:
    """Resolve all subflow references from the root flow's directory."""
    flows = [root_flow]
    for state in root_flow.states:
        if state.flow is not None:
            subflow_path = root_path.parent / state.flow
            if subflow_path.exists():
                flows.append(load_flow_from_file(subflow_path))
    return flows


def _dict_to_flow(raw: dict[str, Any]) -> Flow:
    """Convert a raw dict from YAML into a Flow domain object."""
    if not isinstance(raw, dict):
        raise FlowParseError("Flow definition must be a mapping")
    for field in ("flow", "version"):
        if field not in raw:
            raise FlowParseError(f"Missing required field: {field}")
    states = [_dict_to_state(s) for s in raw.get("states", [])]
    params = [_dict_to_param(p) for p in raw.get("params", [])]
    return Flow(
        flow=raw["flow"],
        version=raw["version"],
        exits=raw.get("exits", []),
        states=states,
        params=params,
        attrs=raw.get("attrs"),
    )


def _dict_to_state(raw: dict[str, Any]) -> State:
    """Convert a raw dict into a State."""
    if not isinstance(raw, dict):
        raise FlowParseError("State definition must be a mapping")
    if "id" not in raw:
        raise FlowParseError("Missing required field in state: id")

    state_conditions: dict[str, dict[str, str]] | None = None
    raw_conditions = raw.get("conditions")
    if raw_conditions is not None:
        state_conditions = raw_conditions

    next_map: dict[str, Transition] = {}
    for trigger, tdef in raw.get("next", {}).items():
        if isinstance(tdef, str):
            next_map[trigger] = Transition(trigger=trigger, target=tdef)
        elif isinstance(tdef, dict):
            when = tdef.get("when")
            if when is None:
                next_map[trigger] = Transition(
                    trigger=trigger,
                    target=tdef["to"],
                )
            else:
                guard, refs = resolve_when_clause(when, state_conditions, raw["id"])
                next_map[trigger] = Transition(
                    trigger=trigger,
                    target=tdef["to"],
                    conditions=guard,
                    referenced_condition_groups=refs,
                )
    return State(
        id=raw["id"],
        next=next_map,
        flow=raw.get("flow"),
        flow_version=raw.get("flow_version"),
        attrs=raw.get("attrs"),
        conditions=state_conditions,
    )


def _dict_to_param(raw: Any) -> Param:  # noqa: ANN401
    """Convert a raw param into a Param."""
    if isinstance(raw, str):
        return Param(name=raw)
    if isinstance(raw, dict):
        return Param(name=raw["name"], default=raw.get("default"))
    return Param(name=str(raw))


def resolve_when_clause(
    when_clause: dict[str, str] | list | str,
    conditions: dict[str, dict[str, str]] | None,
    state_id: str,
) -> tuple[GuardCondition, frozenset[str] | None]:
    """Resolve a when clause into a GuardCondition and referenced groups."""
    if isinstance(when_clause, dict):
        return GuardCondition(conditions=when_clause), None

    items = [when_clause] if isinstance(when_clause, str) else list(when_clause)
    resolved: dict[str, str] = {}
    referenced: list[str] = []

    for item in items:
        if isinstance(item, str):
            _resolve_named_ref(item, conditions, state_id, resolved, referenced)
        elif isinstance(item, dict):
            resolved.update(item)

    return (
        GuardCondition(conditions=resolved),
        frozenset(referenced) if referenced else None,
    )


def _resolve_named_ref(
    name: str,
    conditions: dict[str, dict[str, str]] | None,
    state_id: str,
    resolved: dict[str, str],
    referenced: list[str],
) -> None:
    """Resolve a single named condition reference into the resolved dict."""
    if conditions is None or name not in conditions:
        raise FlowParseError(
            f"Unknown condition reference '{name}' in state '{state_id}'"
        )
    resolved.update(conditions[name])
    referenced.append(name)
