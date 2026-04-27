"""CLI entrypoint for flowr — invoked via `python -m flowr`."""

import argparse
import importlib.metadata
import sys
from pathlib import Path
from typing import Any

from flowr.cli.output import format_json, format_text
from flowr.domain.condition import evaluate_condition, parse_condition
from flowr.domain.flow_definition import Flow, State, Transition
from flowr.domain.loader import FlowParseError, load_flow_from_file, resolve_subflows
from flowr.domain.mermaid import to_mermaid
from flowr.domain.validation import validate


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    meta = importlib.metadata.metadata("flowr")
    parser = argparse.ArgumentParser(
        prog="flowr",
        description=meta["Summary"],
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"flowr {meta['Version']}",
    )
    _add_subcommands(parser)
    return parser


def _add_flow_args(parser: argparse.ArgumentParser) -> None:
    """Add common args: flow file path and --json flag."""
    parser.add_argument("flow_file", type=Path, help="Path to flow YAML file")
    parser.add_argument("--json", action="store_true", dest="json_output")


def _add_evidence_args(parser: argparse.ArgumentParser) -> None:
    """Add evidence input args."""
    parser.add_argument(
        "--evidence",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Evidence key=value pairs",
    )
    parser.add_argument(
        "--evidence-json",
        default=None,
        metavar="JSON",
        help="JSON evidence object",
    )


def _parse_evidence(args: argparse.Namespace) -> dict[str, str]:
    """Parse evidence from CLI args into a dict."""
    evidence: dict[str, str] = {}
    for pair in args.evidence:
        key, _, value = pair.partition("=")
        evidence[key] = value
    if args.evidence_json is not None:
        import json

        data = json.loads(args.evidence_json)
        for k, v in data.items():
            evidence[k] = str(v)
    return evidence


def _add_subcommands(parser: argparse.ArgumentParser) -> None:
    """Add all CLI subcommands."""
    sub = parser.add_subparsers(dest="command")

    # validate
    p_validate = sub.add_parser("validate", help="Validate a flow definition")
    _add_flow_args(p_validate)

    # states
    p_states = sub.add_parser("states", help="List all states in a flow")
    _add_flow_args(p_states)

    # check
    p_check = sub.add_parser("check", help="Check a state or transition conditions")
    _add_flow_args(p_check)
    p_check.add_argument("state_id", help="State id to inspect")
    p_check.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Target to check conditions for",
    )

    # next
    p_next = sub.add_parser("next", help="Show valid next transitions")
    _add_flow_args(p_next)
    p_next.add_argument("state_id", help="Current state id")
    _add_evidence_args(p_next)

    # transition
    p_transition = sub.add_parser("transition", help="Compute next state")
    _add_flow_args(p_transition)
    p_transition.add_argument("state_id", help="Current state id")
    p_transition.add_argument("trigger", help="Transition trigger")
    _add_evidence_args(p_transition)

    # mermaid
    p_mermaid = sub.add_parser("mermaid", help="Export as Mermaid diagram")
    _add_flow_args(p_mermaid)


def _cmd_validate(args: argparse.Namespace) -> int:
    """Run validate subcommand."""
    flow = load_flow_from_file(args.flow_file)
    all_flows = resolve_subflows(flow, args.flow_file)
    result = validate(flow, all_flows if len(all_flows) > 1 else None)
    output: dict[str, Any] = {
        "valid": result.is_valid,
        "violations": [],
    }
    for v in result.violations:
        output["violations"].append(
            {
                "severity": v.severity.value,
                "message": v.message,
                "location": v.location,
            }
        )
    if args.json_output:
        print(format_json(output))  # noqa: T201
    else:
        print(format_text(output))  # noqa: T201
    return 0 if result.is_valid else 1


def _cmd_states(args: argparse.Namespace) -> int:
    """Run states subcommand."""
    flow = load_flow_from_file(args.flow_file)
    state_ids = [s.id for s in flow.states]
    if args.json_output:
        print(format_json(state_ids))  # noqa: T201
    else:
        for sid in state_ids:
            print(sid)  # noqa: T201
    return 0


def _cmd_check(
    args: argparse.Namespace,
) -> int:
    """Run check subcommand."""
    flow = load_flow_from_file(args.flow_file)
    state = _find_state(flow, args.state_id)
    if state is None:
        _error(f"State '{args.state_id}' not found")
        return 1
    if args.target is not None:
        return _cmd_check_conditions(flow, state, args)
    return _cmd_check_state(flow, state, args)


def _cmd_check_state(flow: Flow, state: State, args: argparse.Namespace) -> int:
    """Show state details."""
    output: dict[str, Any] = {"id": state.id}
    if state.attrs:
        output["attrs"] = state.attrs
    if state.flow:
        output["flow"] = state.flow
    transitions = list(state.next.keys())
    output["transitions"] = transitions
    if args.json_output:
        print(format_json(output))  # noqa: T201
    else:
        print(format_text(output))  # noqa: T201
    return 0


def _cmd_check_conditions(flow: Flow, state: State, args: argparse.Namespace) -> int:
    """Show conditions for a specific transition target."""
    transition = state.next.get(args.target)
    if transition is None:
        _error(f"Transition target '{args.target}' not found in state '{state.id}'")
        return 1
    output: dict[str, Any] = {
        "from": state.id,
        "target": args.target,
    }
    if transition.conditions:
        output["conditions"] = transition.conditions.conditions
    else:
        output["conditions"] = "(none)"
    if args.json_output:
        print(format_json(output))  # noqa: T201
    else:
        print(format_text(output))  # noqa: T201
    return 0


def _cmd_next(args: argparse.Namespace) -> int:
    """Run next subcommand."""
    flow = load_flow_from_file(args.flow_file)
    state = _find_state(flow, args.state_id)
    if state is None:
        _error(f"State '{args.state_id}' not found")
        return 1
    evidence = _parse_evidence(args)
    passing = _find_passing_transitions(state, evidence)
    output: dict[str, Any] = {
        "state": state.id,
        "next": [t.target for t in passing],
    }
    if args.json_output:
        print(format_json(output))  # noqa: T201
    else:
        print(format_text(output))  # noqa: T201
    return 0


def _cmd_transition(args: argparse.Namespace) -> int:
    """Run transition subcommand."""
    flow = load_flow_from_file(args.flow_file)
    all_flows = resolve_subflows(flow, args.flow_file)
    state = _find_state(flow, args.state_id)
    if state is None:
        _error(f"State '{args.state_id}' not found")
        return 1
    transition = state.next.get(args.trigger)
    if transition is None:
        _error(f"Trigger '{args.trigger}' not found in state '{state.id}'")
        return 1
    evidence = _parse_evidence(args)
    if transition.conditions and not _conditions_met(
        transition.conditions.conditions, evidence
    ):
        _error(f"Conditions not met for trigger '{args.trigger}'")
        return 1
    target = transition.target
    target_state = _find_state(flow, target)
    if target_state is not None and target_state.flow is not None:
        child = _find_subflow(all_flows, target_state.flow, args.flow_file)
        if child and child.states:
            target = f"{child.flow}/{child.states[0].id}"
    output: dict[str, Any] = {
        "from": state.id,
        "trigger": args.trigger,
        "to": target,
    }
    if args.json_output:
        print(format_json(output))  # noqa: T201
    else:
        print(format_text(output))  # noqa: T201
    return 0


def _cmd_mermaid(args: argparse.Namespace) -> int:
    """Run mermaid subcommand."""
    flow = load_flow_from_file(args.flow_file)
    diagram = to_mermaid(flow)
    if args.json_output:
        print(format_json({"mermaid": diagram}))  # noqa: T201
    else:
        print(diagram)  # noqa: T201
    return 0


def _find_state(flow: Flow, state_id: str) -> State | None:
    """Find a state by id in a flow."""
    for s in flow.states:
        if s.id == state_id:
            return s
    return None


def _find_passing_transitions(
    state: State, evidence: dict[str, str]
) -> list[Transition]:
    """Find transitions whose conditions pass given evidence."""
    passing: list[Transition] = []
    for _trigger, transition in state.next.items():
        if transition.conditions is None or _conditions_met(
            transition.conditions.conditions, evidence
        ):
            passing.append(transition)
    return passing


def _conditions_met(conditions: dict[str, str], evidence: dict[str, str]) -> bool:
    """Check if all conditions are satisfied by evidence."""
    for key, cond_str in conditions.items():
        ev = evidence.get(key, "")
        op, value = parse_condition(cond_str)
        if not evaluate_condition(op, value, ev):
            return False
    return True


def _find_subflow(all_flows: list[Flow], flow_ref: str, root_path: Path) -> Flow | None:
    """Find a subflow by its flow name from the resolved list."""
    for f in all_flows:
        if f.flow == Path(flow_ref).stem:
            return f
    return None


def _error(msg: str) -> None:
    """Print error to stderr."""
    print(f"error: {msg}", file=sys.stderr)  # noqa: T201


def main() -> None:
    """Run the application."""
    args = build_parser().parse_args()
    if args.command is None:
        build_parser().print_help()
        sys.exit(2)
    cmd_map = {
        "validate": _cmd_validate,
        "states": _cmd_states,
        "check": _cmd_check,
        "next": _cmd_next,
        "transition": _cmd_transition,
        "mermaid": _cmd_mermaid,
    }
    handler = cmd_map.get(args.command)
    if handler is None:  # pragma: no cover
        _error(f"Unknown command: {args.command}")
        sys.exit(2)
    if not args.flow_file.exists():  # pragma: no cover
        _error(f"File not found: {args.flow_file}")
        sys.exit(2)
    try:
        sys.exit(handler(args))
    except FlowParseError as exc:
        _error(f"invalid flow definition: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
