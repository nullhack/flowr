"""Session subcommand group: init, show, set-state.

Parses CLI args, dispatches to domain/infrastructure, formats output.
"""

import argparse
import sys
from typing import NoReturn

from flowr.cli.output import format_json, format_text
from flowr.cli.resolution import DefaultFlowNameResolver, FlowNameNotFoundError
from flowr.domain.loader import load_flow_from_file
from flowr.infrastructure.config import FlowrConfig
from flowr.infrastructure.session_store import (
    SessionAlreadyExistsError,
    SessionNotFoundError,
    YamlSessionStore,
)


def add_session_parser(sub: argparse._SubParsersAction) -> None:
    """Add the session subcommand group to the argument parser."""
    session_parser = sub.add_parser("session", help="Manage workflow sessions")
    session_sub = session_parser.add_subparsers(dest="session_command")

    # session init
    p_init = session_sub.add_parser("init", help="Initialize a new session")
    p_init.add_argument("flow", help="Flow name or file path")
    p_init.add_argument(
        "--name", default=None, help="Session name (default: from config)"
    )

    # session show
    p_show = session_sub.add_parser("show", help="Show current session state")
    p_show.add_argument(
        "--name", default=None, help="Session name (default: from config)"
    )
    p_show.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        dest="output_format",
        help="Output format (default: yaml)",
    )

    # session set-state
    p_set = session_sub.add_parser("set-state", help="Update the current session state")
    p_set.add_argument("state", help="New state ID")
    p_set.add_argument(
        "--name", default=None, help="Session name (default: from config)"
    )


def _error(msg: str) -> NoReturn:  # pragma: no cover — tested via subprocess
    """Print error to stderr and exit with code 1."""
    print(f"error: {msg}", file=sys.stderr)  # noqa: T201
    sys.exit(1)


def cmd_session_init(  # pragma: no cover — tested via subprocess
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> int:
    """Run session init subcommand.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    flows_dir = config.flows_path()
    sessions_dir = config.sessions_path()
    name = args.name or config.default_session

    try:
        flow_path = resolver.resolve(args.flow, flows_dir)
    except FlowNameNotFoundError as exc:
        _error(str(exc))

    store = YamlSessionStore(sessions_dir)

    try:
        session = store.init(flow_path, name)
    except SessionAlreadyExistsError as exc:
        _error(str(exc))

    output = {
        "flow": session.flow,
        "state": session.state,
        "name": session.name,
        "created_at": session.created_at,
    }
    print(format_text(output))  # noqa: T201
    return 0


def cmd_session_show(  # pragma: no cover — tested via subprocess
    args: argparse.Namespace, config: FlowrConfig, _resolver: DefaultFlowNameResolver
) -> int:
    """Run session show subcommand.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    sessions_dir = config.sessions_path()
    name = args.name or config.default_session

    store = YamlSessionStore(sessions_dir)
    try:
        session = store.load(name)
    except SessionNotFoundError as exc:
        _error(str(exc))

    output: dict = {
        "flow": session.flow,
        "state": session.state,
        "name": session.name,
        "stack": [{"flow": f.flow, "state": f.state} for f in session.stack],
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }

    if args.output_format == "json":
        print(format_json(output))  # noqa: T201
    else:
        print(format_text(output))  # noqa: T201
    return 0


def cmd_session_set_state(  # pragma: no cover — tested via subprocess
    args: argparse.Namespace, config: FlowrConfig, resolver: DefaultFlowNameResolver
) -> int:
    """Run session set-state subcommand.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    sessions_dir = config.sessions_path()
    name = args.name or config.default_session

    store = YamlSessionStore(sessions_dir)
    try:
        session = store.load(name)
    except SessionNotFoundError as exc:
        _error(str(exc))

    # Validate that the requested state exists in the flow
    flows_dir = config.flows_path()
    try:
        flow_path = resolver.resolve(session.flow, flows_dir)
    except FlowNameNotFoundError as exc:
        _error(str(exc))

    flow = load_flow_from_file(flow_path)
    state_ids = {s.id for s in flow.states}
    if args.state not in state_ids:
        _error(f"State '{args.state}' not found in flow '{session.flow}'")

    updated = session.with_state(args.state)
    store.save(updated)

    output = {
        "flow": updated.flow,
        "state": updated.state,
        "updated_at": updated.updated_at,
    }
    print(format_text(output))  # noqa: T201
    return 0
