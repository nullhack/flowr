"""Session subcommand group: init, show, set-state.

Parses CLI args, dispatches to domain/infrastructure, formats output.
"""

import argparse
import sys
from typing import NoReturn

from flowr.cli.output import format_json, format_text


def add_session_parser(sub: argparse._SubParsersAction) -> None:
    """Add the session subcommand group to the argument parser."""
    session_parser = sub.add_parser("session", help="Manage workflow sessions")
    session_sub = session_parser.add_subparsers(dest="session_command")

    # session init
    p_init = session_sub.add_parser("init", help="Initialize a new session")
    p_init.add_argument("flow", help="Flow name or file path")
    p_init.add_argument("--name", default=None, help="Session name (default: from config)")

    # session show
    p_show = session_sub.add_parser("show", help="Show current session state")
    p_show.add_argument("--name", default=None, help="Session name (default: from config)")
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
    p_set.add_argument("--name", default=None, help="Session name (default: from config)")


def _error(msg: str) -> NoReturn:
    """Print error to stderr and exit with code 1."""
    print(f"error: {msg}", file=sys.stderr)  # noqa: T201
    sys.exit(1)


def cmd_session_init(args: argparse.Namespace) -> int:
    """Run session init subcommand."""
    raise NotImplementedError


def cmd_session_show(args: argparse.Namespace) -> int:
    """Run session show subcommand."""
    raise NotImplementedError


def cmd_session_set_state(args: argparse.Namespace) -> int:
    """Run session set-state subcommand."""
    raise NotImplementedError