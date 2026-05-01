"""Session format for tracking workflow progress."""

from dataclasses import dataclass, field
from datetime import datetime
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
    name: str = "default"
    created_at: str = ""
    updated_at: str = ""
    stack: list[SessionStackFrame] = field(default_factory=list)
    params: dict[str, dict[str, Any]] = field(default_factory=dict)

    def with_state(self, state: str, updated_at: str | None = None) -> "Session":
        """Return a new Session with an updated state and optional timestamp."""
        ts = updated_at or datetime.now(tz=None).isoformat()
        return Session(
            flow=self.flow,
            state=state,
            name=self.name,
            created_at=self.created_at,
            updated_at=ts,
            stack=self.stack,
            params=self.params,
        )

    def push_stack(self, frame: SessionStackFrame, new_state: str) -> "Session":
        """Push a stack frame and update state (entering a subflow)."""
        ts = datetime.now(tz=None).isoformat()
        return Session(
            flow=self.flow,
            state=new_state,
            name=self.name,
            created_at=self.created_at,
            updated_at=ts,
            stack=[*self.stack, frame],
            params=self.params,
        )

    def pop_stack(self, new_state: str) -> "Session":
        """Pop a stack frame and update state (exiting a subflow)."""
        ts = datetime.now(tz=None).isoformat()
        return Session(
            flow=self.flow,
            state=new_state,
            name=self.name,
            created_at=self.created_at,
            updated_at=ts,
            stack=self.stack[:-1],
            params=self.params,
        )
