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
    """Add common args: flow file path and --text flag."""
    parser.add_argument("flow_file", help="Path to flow YAML file or flow name")
    parser.add_argument("--text", action="store_true", dest="text_output")


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
    p_validate.add_argument(
        "flow_file",
        nargs="?",
        default=None,
        help="Path to flow YAML file or flow name (required unless --session)",
    )
    p_validate.add_argument("--text", action="store_true", dest="text_output")
    p_validate.add_argument(
        "--session",
        nargs="?",
        const="__default__",
        default=None,
        dest="session",
        metavar="NAME",
        help="Use session name to resolve flow (read-only)",
    )

    # states
    p_states = sub.add_parser("states", help="List all states in a flow")
    p_states.add_argument(
        "flow_file",
        nargs="?",
        default=None,
        help="Path to flow YAML file or flow name (required unless --session)",
    )
    p_states.add_argument("--text", action="store_true", dest="text_output")
    p_states.add_argument(
        "--session",
        nargs="?",
        const="__default__",
        default=None,
        dest="session",
        metavar="NAME",
        help="Use session name to resolve flow (read-only)",
    )

    # check
    p_check = sub.add_parser("check", help="Check a state or transition conditions")
    p_check.add_argument(
        "flow_file",
        nargs="?",
        default=None,
        help="Path to flow YAML file or flow name (required unless --session)",
    )
    p_check.add_argument("--text", action="store_true", dest="text_output")
    p_check.add_argument(
        "state_id",
        nargs="?",
        default=None,
        help="State id to inspect",
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
        "flow_file",
        nargs="?",
        default=None,
        help="Path to flow YAML file or flow name (required unless --session)",
    )
    p_next.add_argument("--text", action="store_true", dest="text_output")
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
    p_transition.add_argument("--text", action="store_true", dest="text_output")
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
        "--text",
        action="store_true",
        dest="text_output",
        help="Output as human-readable text",
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
    if args.flow_file is None:
        _error("flow_file is required when not using --session")
        return 2
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
    if args.text_output:
        print(format_text(output))  # noqa: T201
    else:
        print(format_json(output))  # noqa: T201
    return 0 if result.is_valid else 1


def _cmd_states(args: argparse.Namespace) -> int:
    """Run states subcommand.

    Returns:
        Exit code: 0 on success.
    """
    if args.flow_file is None:
        _error("flow_file is required when not using --session")
        return 2
    flow = load_flow_from_file(args.flow_file)
    state_ids = [s.id for s in flow.states]
    if args.text_output:
        for sid in state_ids:
            print(sid)  # noqa: T201
    else:
        print(format_json(state_ids))  # noqa: T201
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
    if args.text_output:
        print(format_text(output))  # noqa: T201
    else:
        print(format_json(output))  # noqa: T201
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
    if args.text_output:
        print(format_text(output))  # noqa: T201
    else:
        print(format_json(output))  # noqa: T201
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
    transitions = _build_transition_list(state, evidence)
    if args.text_output:
        print(_format_transitions_text(state.id, transitions))  # noqa: T201
    else:
        print(format_json({"state": state.id, "transitions": transitions}))  # noqa: T201
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
    if args.text_output:
        print(format_text(output))  # noqa: T201
    else:
        print(format_json(output))  # noqa: T201
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
            "value": _display_path(config.project_root),
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
    if args.text_output:
        for row in rows:
            print(f"{row['key']} = {row['value']}  ({row['source']})")  # noqa: T201
    else:
        print(format_json(rows))  # noqa: T201
    return 0


def _cmd_mermaid(args: argparse.Namespace) -> int:
    """Run mermaid subcommand.

    Returns:
        Exit code: 0 on success.
    """
    flow = load_flow_from_file(args.flow_file)
    diagram = to_mermaid(flow)
    if args.text_output:
        print(diagram)  # noqa: T201
    else:
        print(format_json({"mermaid": diagram}))  # noqa: T201
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


def _build_transition_list(
    state: State, evidence: dict[str, str]
) -> list[dict[str, Any]]:
    """Build rich transition info for all transitions from a state.

    Returns:
        List of dicts with trigger, target, status, and conditions.
    """
    transitions: list[dict[str, Any]] = []
    for trigger, transition in state.next.items():
        if transition.conditions is None or _conditions_met(
            transition.conditions.conditions, evidence
        ):
            status = "open"
        else:
            status = "blocked"
        transitions.append(
            {
                "trigger": trigger,
                "target": transition.target,
                "status": status,
                "conditions": transition.conditions.conditions
                if transition.conditions
                else None,
            }
        )
    return transitions


def _format_transitions_text(state_id: str, transitions: list[dict[str, Any]]) -> str:
    """Format transitions as human-readable text."""
    lines = [f"state: {state_id}"]
    for t in transitions:
        marker = " [blocked]" if t["status"] == "blocked" else ""
        cond = ""
        if t["status"] == "blocked" and t["conditions"]:
            pairs = ", ".join(f"{k}={v}" for k, v in t["conditions"].items())
            cond = f"  need: {pairs}"
        lines.append(f"  {t['trigger']} → {t['target']}{marker}{cond}")
    return "\n".join(lines)


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


def _display_path(path: Path) -> str:
    """Display a path relative to cwd, or '.' if same."""
    try:
        rel = path.relative_to(Path.cwd())
        return "." if rel == Path() else str(rel)
    except ValueError:
        return str(path)


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
    except FlowParseError as exc:  # pragma: no cover
        _error(f"invalid flow definition: {exc}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover

    return session, flow, flow_path


def _find_flow_file(flow_name: str, flows_dir: Path) -> Path | None:
    """Find a flow file by name in the flows directory."""
    path = flows_dir / (flow_name + ".yaml")
    if path.exists():
        return path
    path = flows_dir / flow_name
    if path.exists():
        return path
    return None


def _enter_subflow(
    session: Session,
    parent_flow: Flow,
    parent_flow_path: Path,
    target_state_id: str,
) -> tuple[Session, str] | None:
    """Try to enter a subflow for the given target state.

    Returns (updated_session, display_target) if a subflow was entered,
    or None if the target is not a subflow entry point.

    Recursively enters nested subflows if the child's first state
    is itself a subflow wrapper (has a ``flow:`` field).
    """
    target_state = _find_state(parent_flow, target_state_id)
    if target_state is None or target_state.flow is None:
        return None

    all_flows = resolve_subflows(parent_flow, parent_flow_path)
    child = _find_subflow(all_flows, target_state.flow, parent_flow_path)
    if child is None or not child.states:
        return None

    frame = SessionStackFrame(flow=parent_flow.flow, state=target_state_id)
    subflow_initial = child.states[0].id
    updated = session.push_stack(frame, subflow_initial, new_flow=child.flow)
    display = f"{child.flow}/{subflow_initial}"

    child_first = child.states[0]
    if child_first.flow is not None:
        child_flows = resolve_subflows(child, parent_flow_path)
        grandchild = _find_subflow(child_flows, child_first.flow, parent_flow_path)
        if grandchild is not None and grandchild.states:
            nested_frame = SessionStackFrame(flow=child.flow, state=subflow_initial)
            gc_initial = grandchild.states[0].id
            nested = updated.push_stack(
                nested_frame, gc_initial, new_flow=grandchild.flow
            )
            return nested, f"{grandchild.flow}/{gc_initial}"

    return updated, display


def _resolve_subflow_exit(
    session: Session,
    trigger: str,
    exit_name: str,
    flows_dir: Path,
) -> tuple[Session, str]:
    """Handle subflow exit: resolve parent transition, handle chaining.

    When a transition targets an exit name and the session has a stack,
    this function resolves the actual target through the parent flow's
    transition map and handles entering the next subflow if needed.
    """
    parent_frame = session.stack[-1]
    parent_flow_path = _find_flow_file(parent_frame.flow, flows_dir)
    if parent_flow_path is None:
        return session.pop_stack(exit_name), exit_name

    parent_flow = load_flow_from_file(parent_flow_path)
    parent_state = _find_state(parent_flow, parent_frame.state)
    if parent_state is None:
        return session.pop_stack(exit_name), exit_name

    parent_transition = parent_state.next.get(exit_name)
    if parent_transition is None:
        return session.pop_stack(exit_name), exit_name

    resolved_target = parent_transition.target

    popped = session.pop_stack(resolved_target)

    entry = _enter_subflow(popped, parent_flow, parent_flow_path, resolved_target)
    if entry is not None:
        return entry

    return popped, resolved_target


def _apply_session_transition(
    session: Session,
    flow: Flow,
    flow_path: Path,
    trigger: str,
    evidence: dict[str, str],
    flows_dir: Path | None = None,
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
    ):  # pragma: no cover
        _error(f"Conditions not met for trigger '{trigger}'")  # pragma: no cover
        sys.exit(1)  # pragma: no cover

    target = transition.target

    # Check if transition enters a subflow
    entry = _enter_subflow(session, flow, flow_path, target)
    if entry is not None:
        return entry

    # Check if transition exits a subflow
    if session.stack and target in flow.exits:
        if flows_dir is not None:
            return _resolve_subflow_exit(session, trigger, target, flows_dir)
        updated_session = session.pop_stack(target)
        return updated_session, target

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
        session, flow, flow_path, trigger, evidence, config.flows_path()
    )

    store = YamlSessionStore(config.sessions_path())
    store.save(updated_session)

    output: dict[str, Any] = {
        "from": session.state,
        "trigger": trigger,
        "to": target,
    }
    if args.text_output:
        print(format_text(output))  # noqa: T201
    else:
        print(format_json(output))  # noqa: T201
    sys.exit(0)


def _handle_session(
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> None:
    """Dispatch session subcommands."""
    if args.session_command is None:  # pragma: no cover
        build_parser().parse_args(["session", "--help"])
        sys.exit(2)  # pragma: no cover

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
    except FlowParseError as exc:  # pragma: no cover
        _error(f"invalid flow definition: {exc}")  # pragma: no cover
        sys.exit(1)  # pragma: no cover
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

    effective_target = args.target or getattr(args, "flow_file", None)
    if effective_target is not None:
        args.target = effective_target
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
    transitions = _build_transition_list(state, evidence)
    if args.text_output:
        print(_format_transitions_text(state.id, transitions))  # noqa: T201
    else:
        print(format_json({"state": state.id, "transitions": transitions}))  # noqa: T201
    sys.exit(0)


def _cmd_states_session(
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> None:
    """Run states with session-aware flow resolution (read-only)."""
    session_name = (
        config.default_session if args.session == "__default__" else args.session
    )

    _session, flow, _flow_path = _resolve_session(session_name, config, resolver)
    state_ids = [s.id for s in flow.states]
    if args.text_output:
        for sid in state_ids:
            print(sid)  # noqa: T201
    else:
        print(format_json(state_ids))  # noqa: T201
    sys.exit(0)


def _cmd_validate_session(
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> None:
    """Run validate with session-aware flow resolution (read-only)."""
    session_name = (
        config.default_session if args.session == "__default__" else args.session
    )

    _session, flow, flow_path = _resolve_session(session_name, config, resolver)
    all_flows = resolve_subflows(flow, flow_path)
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
    if args.text_output:
        print(format_text(output))  # noqa: T201
    else:
        print(format_json(output))  # noqa: T201
    sys.exit(0 if result.is_valid else 1)


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


_SESSION_COMMANDS = {
    "transition": "_cmd_transition_session",
    "check": "_cmd_check_session",
    "next": "_cmd_next_session",
    "states": "_cmd_states_session",
    "validate": "_cmd_validate_session",
}


def _dispatch_session_command(
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> bool:
    """Handle session-aware command dispatch. Returns True if handled."""
    if getattr(args, "session", None) is None:
        return False
    handler_name = _SESSION_COMMANDS.get(args.command)
    if handler_name is None:
        return False
    handler = globals()[handler_name]
    handler(args, config, resolver)
    return True


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

    if args.command == "session":  # pragma: no cover
        _handle_session(args, config, resolver)
        return  # pragma: no cover

    if args.command == "config":  # pragma: no cover
        rc = _cmd_config(args)
        sys.exit(rc)  # pragma: no cover

    if _dispatch_session_command(args, config, resolver):
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
