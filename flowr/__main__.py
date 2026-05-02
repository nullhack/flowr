"""CLI entrypoint for flowr — invoked via `python -m flowr`."""

import argparse
import importlib.metadata
import sys
from pathlib import Path
from typing import Any

from flowr.cli.output import format_json, format_text
from flowr.cli.resolution import DefaultFlowNameResolver, FlowNameNotFoundError
from flowr.cli.session_cmd import (
    add_session_parser,
    cmd_session_init,
    cmd_session_list,
    cmd_session_set_state,
    cmd_session_show,
)
from flowr.domain.condition import evaluate_condition, parse_condition
from flowr.domain.flow_definition import Flow, State, Transition
from flowr.domain.loader import FlowParseError, load_flow_from_file, resolve_subflows
from flowr.domain.mermaid import to_mermaid
from flowr.domain.session import Session, SessionStackFrame
from flowr.domain.validation import validate
from flowr.infrastructure.config import (
    FlowrConfig,
    resolve_config,
    resolve_config_with_sources,
)
from flowr.infrastructure.session_store import (
    SessionNameNotFoundError,
    SessionNotFoundError,
    YamlSessionStore,
)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser.

    Returns:
        The configured ArgumentParser instance.
    """
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
    parser.add_argument(
        "--flows-dir",
        dest="flows_dir",
        default=None,
        metavar="DIR",
        help="Override the configured flows directory for this invocation",
    )
    _add_subcommands(parser)
    return parser


def _add_flow_args(parser: argparse.ArgumentParser) -> None:
    """Add common args: flow file path and --json flag."""
    parser.add_argument("flow_file", help="Path to flow YAML file or flow name")
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
    """Parse evidence from CLI args into a dict.

    Returns:
        Dictionary mapping evidence keys to their string values.
    """
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
    p_check.add_argument(
        "flow_file", nargs="?", default=None,
        help="Path to flow YAML file or flow name (required unless --session)",
    )
    p_check.add_argument("--json", action="store_true", dest="json_output")
    p_check.add_argument(
        "state_id", nargs="?", default=None, help="State id to inspect",
    )
    p_check.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Target to check conditions for",
    )
    p_check.add_argument(
        "--session",
        nargs="?",
        const="__default__",
        default=None,
        dest="session",
        metavar="NAME",
        help="Use session name or file path to resolve flow/state (read-only)",
    )

    # next
    p_next = sub.add_parser("next", help="Show valid next transitions")
    p_next.add_argument(
        "flow_file", nargs="?", default=None,
        help="Path to flow YAML file or flow name (required unless --session)",
    )
    p_next.add_argument("--json", action="store_true", dest="json_output")
    p_next.add_argument("state_id", nargs="?", default=None, help="Current state id")
    _add_evidence_args(p_next)
    p_next.add_argument(
        "--session",
        nargs="?",
        const="__default__",
        default=None,
        dest="session",
        metavar="NAME",
        help="Use session name or file path to resolve flow/state (read-only)",
    )

    # transition
    p_transition = sub.add_parser("transition", help="Compute next state")
    p_transition.add_argument(
        "positional",
        nargs="*",
        help="Args: <flow> <state> <trigger> or <trigger> with --session",
    )
    p_transition.add_argument("--json", action="store_true", dest="json_output")
    _add_evidence_args(p_transition)
    p_transition.add_argument(
        "--session",
        nargs="?",
        const="__default__",
        default=None,
        dest="session",
        metavar="NAME",
        help="Use session to resolve flow/state; auto-update after transition",
    )

    # config
    p_config = sub.add_parser("config", help="Show resolved configuration")
    p_config.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON",
    )

    # mermaid
    p_mermaid = sub.add_parser("mermaid", help="Export as Mermaid diagram")
    _add_flow_args(p_mermaid)

    # session
    add_session_parser(sub)


def _cmd_validate(args: argparse.Namespace) -> int:
    """Run validate subcommand.

    Returns:
        Exit code: 0 if valid, 1 if invalid.
    """
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
    """Run states subcommand.

    Returns:
        Exit code: 0 on success.
    """
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
    """Run check subcommand.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    if args.flow_file is None:
        _error("flow_file is required when not using --session")
        return 2
    if args.state_id is None:
        _error("state_id is required when not using --session")
        return 2
    flow = load_flow_from_file(args.flow_file)
    state = _find_state(flow, args.state_id)
    if state is None:
        _error(f"State '{args.state_id}' not found")
        return 1
    if args.target is not None:
        return _cmd_check_conditions(flow, state, args)
    return _cmd_check_state(flow, state, args)


def _cmd_check_state(_flow: Flow, state: State, args: argparse.Namespace) -> int:
    """Show state details.

    Returns:
        Exit code: 0 on success.
    """
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


def _cmd_check_conditions(_flow: Flow, state: State, args: argparse.Namespace) -> int:
    """Show conditions for a specific transition target.

    Returns:
        Exit code: 0 on success, 1 if target not found.
    """
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
    """Run next subcommand.

    Returns:
        Exit code: 0 on success, 1 if state not found.
    """
    if args.flow_file is None:
        _error("flow_file is required when not using --session")
        return 2
    if args.state_id is None:
        _error("state_id is required when not using --session")
        return 2
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
    """Run transition subcommand.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    if hasattr(args, "positional") and args.positional:
        flow_file = args.flow_file
        state_id = args.positional[1]
        trigger = args.positional[2]
    else:
        flow_file = args.flow_file
        state_id = args.state_id
        trigger = args.trigger
    flow = load_flow_from_file(flow_file)
    all_flows = resolve_subflows(flow, flow_file)
    state = _find_state(flow, state_id)
    if state is None:
        _error(f"State '{state_id}' not found")
        return 1
    transition = state.next.get(trigger)
    if transition is None:
        _error(f"Trigger '{trigger}' not found in state '{state_id}'")
        return 1
    evidence = _parse_evidence(args)
    if transition.conditions and not _conditions_met(
        transition.conditions.conditions, evidence
    ):
        _error(f"Conditions not met for trigger '{trigger}'")
        return 1
    target = transition.target
    target_state = _find_state(flow, target)
    if target_state is not None and target_state.flow is not None:
        child = _find_subflow(all_flows, target_state.flow, Path(flow_file))
        if child and child.states:
            target = f"{child.flow}/{child.states[0].id}"
    output: dict[str, Any] = {
        "from": state_id,
        "trigger": trigger,
        "to": target,
    }
    if args.json_output:
        print(format_json(output))  # noqa: T201
    else:
        print(format_text(output))  # noqa: T201
    return 0


def _cmd_config(args: argparse.Namespace) -> int:
    """Run config subcommand — show resolved configuration with sources.

    Returns:
        Exit code: 0 on success.
    """
    config, sources = resolve_config_with_sources(
        cli_overrides={"flows_dir": args.flows_dir} if args.flows_dir else None,
    )
    rows = [
        {
            "key": "project_root",
            "value": str(config.project_root),
            "source": sources["project_root"],
        },
        {
            "key": "flows_dir",
            "value": str(config.flows_dir),
            "source": sources["flows_dir"],
        },
        {
            "key": "sessions_dir",
            "value": str(config.sessions_dir),
            "source": sources["sessions_dir"],
        },
        {
            "key": "default_flow",
            "value": config.default_flow,
            "source": sources["default_flow"],
        },
        {
            "key": "default_session",
            "value": config.default_session,
            "source": sources["default_session"],
        },
    ]
    if args.json_output:
        print(format_json(rows))  # noqa: T201
    else:
        for row in rows:
            print(f"{row['key']} = {row['value']}  ({row['source']})")  # noqa: T201
    return 0


def _cmd_mermaid(args: argparse.Namespace) -> int:
    """Run mermaid subcommand.

    Returns:
        Exit code: 0 on success.
    """
    flow = load_flow_from_file(args.flow_file)
    diagram = to_mermaid(flow)
    if args.json_output:
        print(format_json({"mermaid": diagram}))  # noqa: T201
    else:
        print(diagram)  # noqa: T201
    return 0


def _find_state(flow: Flow, state_id: str) -> State | None:
    """Find a state by id in a flow.

    Returns:
        The matching State, or None if not found.
    """
    for s in flow.states:
        if s.id == state_id:
            return s
    return None


def _find_passing_transitions(
    state: State, evidence: dict[str, str]
) -> list[Transition]:
    """Find transitions whose conditions pass given evidence.

    Returns:
        List of transitions whose conditions are satisfied.
    """
    passing: list[Transition] = []
    for _trigger, transition in state.next.items():
        if transition.conditions is None or _conditions_met(
            transition.conditions.conditions, evidence
        ):
            passing.append(transition)
    return passing


def _conditions_met(conditions: dict[str, str], evidence: dict[str, str]) -> bool:
    """Check if all conditions are satisfied by evidence.

    Returns:
        True if all conditions pass, False otherwise.
    """
    for key, cond_str in conditions.items():
        ev = evidence.get(key, "")
        op, value = parse_condition(cond_str)
        if not evaluate_condition(op, value, ev):
            return False
    return True


def _find_subflow(
    all_flows: list[Flow], flow_ref: str, _root_path: Path
) -> Flow | None:
    """Find a subflow by its flow name from the resolved list.

    Returns:
        The matching Flow, or None if not found.
    """
    for f in all_flows:
        if f.flow == Path(flow_ref).stem:
            return f
    return None


def _error(msg: str) -> None:
    """Print error to stderr."""
    print(f"error: {msg}", file=sys.stderr)  # noqa: T201


def _resolve_session(
    session_name: str, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> tuple[Session, Flow, Path]:
    """Load session and resolve its flow.

    Returns:
        Tuple of (session, flow, flow_path).
    """
    store = YamlSessionStore(config.sessions_path())
    try:
        session = store.load(session_name)
    except (SessionNotFoundError, SessionNameNotFoundError) as exc:
        _error(str(exc))
        sys.exit(1)

    try:
        flow_path = resolver.resolve(session.flow, config.flows_path())
    except FlowNameNotFoundError as exc:
        _error(str(exc))
        sys.exit(1)

    try:
        flow = load_flow_from_file(flow_path)
    except FlowParseError as exc:
        _error(f"invalid flow definition: {exc}")
        sys.exit(1)

    return session, flow, flow_path


def _apply_session_transition(
    session: Session,
    flow: Flow,
    flow_path: Path,
    trigger: str,
    evidence: dict[str, str],
) -> tuple[Session, str]:
    """Apply a transition to a session, handling subflow push/pop.

    Returns:
        Tuple of (updated_session, target_display).
    """
    state = _find_state(flow, session.state)
    if state is None:
        _error(f"State '{session.state}' not found")
        sys.exit(1)

    transition = state.next.get(trigger)
    if transition is None:
        _error(f"Trigger '{trigger}' not found in state '{session.state}'")
        sys.exit(1)

    if transition.conditions and not _conditions_met(
        transition.conditions.conditions, evidence
    ):
        _error(f"Conditions not met for trigger '{trigger}'")
        sys.exit(1)

    target = transition.target
    all_flows = resolve_subflows(flow, flow_path)
    target_state = _find_state(flow, target)

    # Check if transition enters a subflow
    enters_subflow = target_state is not None and target_state.flow is not None

    if enters_subflow and target_state is not None and target_state.flow is not None:
        flow_ref = target_state.flow
        child = _find_subflow(all_flows, flow_ref, flow_path)
        if child and child.states:
            frame = SessionStackFrame(flow=session.flow, state=session.state)
            subflow_initial = child.states[0].id
            updated_session = session.push_stack(
                frame, subflow_initial, new_flow=child.flow
            )
            target = f"{child.flow}/{subflow_initial}"
        else:
            updated_session = session.with_state(target)
    elif session.stack and target in flow.exits:
        # Transition exits a subflow
        updated_session = session.pop_stack(target)
    else:
        updated_session = session.with_state(target)

    return updated_session, target


def _cmd_transition_session(
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> None:
    """Run transition with session-aware flow/state resolution and auto-update."""
    if not args.positional:
        _error("trigger is required")
        sys.exit(2)
    trigger = args.positional[0]

    session_name = (
        config.default_session if args.session == "__default__" else args.session
    )

    session, flow, flow_path = _resolve_session(session_name, config, resolver)
    evidence = _parse_evidence(args)
    updated_session, target = _apply_session_transition(
        session, flow, flow_path, trigger, evidence
    )

    store = YamlSessionStore(config.sessions_path())
    store.save(updated_session)

    output: dict[str, Any] = {
        "from": session.state,
        "trigger": trigger,
        "to": target,
    }
    if args.json_output:
        print(format_json(output))  # noqa: T201
    else:
        print(format_text(output))  # noqa: T201
    sys.exit(0)


def _handle_session(
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> None:
    """Dispatch session subcommands."""
    if args.session_command is None:
        build_parser().parse_args(["session", "--help"])
        sys.exit(2)

    handlers = {
        "init": cmd_session_init,
        "show": cmd_session_show,
        "set-state": cmd_session_set_state,
        "list": cmd_session_list,
    }
    handler = handlers.get(args.session_command)
    if handler is None:
        _error(f"Unknown session command: {args.session_command}")
        sys.exit(2)

    try:
        rc = handler(args, config, resolver)
    except FlowParseError as exc:
        _error(f"invalid flow definition: {exc}")
        sys.exit(1)
    sys.exit(rc)


def _cmd_check_session(
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> None:
    """Run check with session-aware flow/state resolution (read-only)."""
    session_name = (
        config.default_session if args.session == "__default__" else args.session
    )

    session, flow, _flow_path = _resolve_session(session_name, config, resolver)
    state = _find_state(flow, session.state)
    if state is None:
        _error(f"State '{session.state}' not found")
        sys.exit(1)

    if args.target is not None:
        rc = _cmd_check_conditions(flow, state, args)
    else:
        rc = _cmd_check_state(flow, state, args)
    sys.exit(rc)


def _cmd_next_session(
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> None:
    """Run next with session-aware flow/state resolution (read-only)."""
    session_name = (
        config.default_session if args.session == "__default__" else args.session
    )

    session, flow, _flow_path = _resolve_session(session_name, config, resolver)
    state = _find_state(flow, session.state)
    if state is None:
        _error(f"State '{session.state}' not found")
        sys.exit(1)

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
    sys.exit(0)


def _resolve_flow_for_command(
    args: argparse.Namespace,
    config: FlowrConfig,
    resolver: DefaultFlowNameResolver,
) -> None:
    """Resolve flow_file for non-session, non-transition-session commands."""
    flows_dir = config.flows_path()
    if args.command == "transition":
        if len(args.positional) < 3:
            _error("transition requires <flow> <state> <trigger>")
            sys.exit(2)
        flow_file_arg = args.positional[0]
        try:
            args.flow_file = resolver.resolve(flow_file_arg, flows_dir)
        except FlowNameNotFoundError as exc:
            _error(str(exc))
            sys.exit(1)
    else:
        try:
            args.flow_file = resolver.resolve(args.flow_file, flows_dir)
        except FlowNameNotFoundError as exc:
            _error(str(exc))
            sys.exit(1)


def main() -> None:
    """Run the application."""
    args = build_parser().parse_args()
    if args.command is None:  # pragma: no cover
        build_parser().print_help()
        sys.exit(2)

    resolver = DefaultFlowNameResolver()
    config = resolve_config()
    if args.flows_dir is not None:
        config = resolve_config(cli_overrides={"flows_dir": args.flows_dir})

    if args.command == "session":
        _handle_session(args, config, resolver)
        return

    if args.command == "config":
        rc = _cmd_config(args)
        sys.exit(rc)

    if args.command == "transition" and args.session is not None:
        _cmd_transition_session(args, config, resolver)
        return

    if args.command == "check" and args.session is not None:
        _cmd_check_session(args, config, resolver)
        return

    if args.command == "next" and args.session is not None:
        _cmd_next_session(args, config, resolver)
        return

    _resolve_flow_for_command(args, config, resolver)

    cmd_map = {
        "validate": _cmd_validate,
        "states": _cmd_states,
        "check": _cmd_check,
        "next": _cmd_next,
        "transition": _cmd_transition,
        "mermaid": _cmd_mermaid,
        "config": _cmd_config,
    }
    handler = cmd_map.get(args.command)
    if handler is None:  # pragma: no cover
        _error(f"Unknown command: {args.command}")
        sys.exit(2)
    try:
        sys.exit(handler(args))
    except FlowParseError as exc:
        _error(f"invalid flow definition: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
