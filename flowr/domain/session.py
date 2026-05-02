"""Session format for tracking workflow progress."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


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
        """Return a new Session with an updated state and optional timestamp.

        Returns:
            New Session with the state and updated_at fields changed.
        """
        ts = updated_at or datetime.now(tz=UTC).isoformat()
        return Session(
            flow=self.flow,
            state=state,
            name=self.name,
            created_at=self.created_at,
            updated_at=ts,
            stack=self.stack,
            params=self.params,
        )

    def push_stack(
        self, frame: SessionStackFrame, new_state: str, new_flow: str | None = None
    ) -> "Session":
        """Push a stack frame and update state (entering a subflow).

        Returns:
            New Session with the frame pushed and state/flow updated.
        """
        ts = datetime.now(tz=UTC).isoformat()
        return Session(
            flow=new_flow if new_flow is not None else self.flow,
            state=new_state,
            name=self.name,
            created_at=self.created_at,
            updated_at=ts,
            stack=[*self.stack, frame],
            params=self.params,
        )

    def pop_stack(self, new_state: str) -> "Session":
        """Pop a stack frame and update state (exiting a subflow).

        Returns:
            New Session with the frame popped and state/flow restored.
        """
        ts = datetime.now(tz=UTC).isoformat()
        parent_flow = self.stack[-1].flow if self.stack else self.flow
        return Session(
            flow=parent_flow,
            state=new_state,
            name=self.name,
            created_at=self.created_at,
            updated_at=ts,
            stack=self.stack[:-1],
            params=self.params,
        )


class SessionStore(Protocol):
    """Persistence interface for session state.

    Implementations must use atomic writes (temp-file-then-rename)
    to prevent partial state corruption.
    """

    def init(self, flow_path: Path, name: str) -> Session:
        """Create a new session at the flow's initial state.

        Args:
            flow_path: The resolved path to the flow YAML file.
            name: The session name (used as filename stem).

        Returns:
            The newly created Session.

        Raises:
            SessionAlreadyExistsError: A session with this name already exists.
        """
        ...

    def load(self, name: str) -> Session:
        """Load a session by name.

        Args:
            name: The session name.

        Returns:
            The loaded Session.

        Raises:
            SessionNotFoundError: No session file exists for this name.
        """
        ...

    def save(self, session: Session) -> None:
        """Persist a session using atomic write.

        Args:
            session: The session to save.
        """
        ...

    def list_sessions(self) -> list[Session]:
        """List all sessions in the session store.

        Returns:
            List of all sessions, sorted by updated_at descending.
        """
        ...
