"""Session format for tracking workflow progress."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SessionStackFrame:
    """A frame in the session call stack tracking subflow nesting."""

    flow: str
    state: str


@dataclass(frozen=True, slots=True)
class Session:
    """Minimal session tracking: current flow, state, and call stack."""

    flow: str
    state: str
    stack: list[SessionStackFrame] = field(default_factory=list)
    params: dict[str, dict[str, Any]] = field(default_factory=dict)
