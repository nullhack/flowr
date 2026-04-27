"""Mermaid stateDiagram-v2 conversion for flow definitions."""

from flowr.domain.flow_definition import Flow


def to_mermaid(flow: Flow) -> str:
    """Convert a flow definition to a Mermaid stateDiagram-v2 string."""
    lines = ["stateDiagram-v2"]
    for state in flow.states:
        if state.flow is not None:
            lines.extend(
                [
                    f"    {state.id} --> {state.flow}",
                    f"    note right of {state.id}: invokes {state.flow}",
                ]
            )
        lines.append(f'    state "{state.id}" as {state.id}')
    for state in flow.states:
        for trigger, transition in state.next.items():
            label_parts: list[str] = [trigger]
            if transition.conditions is not None:
                cond_parts = [
                    f"{k}: {v}" for k, v in transition.conditions.conditions.items()
                ]
                label_parts.append(", ".join(cond_parts))
            label = " | ".join(label_parts)
            lines.append(f"    {state.id} --> {transition.target} : {label}")
    return "\n".join(lines)
