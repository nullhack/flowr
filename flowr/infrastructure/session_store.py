"""Session persistence: load/save session YAML files with atomic writes.

Implements the SessionStore Protocol defined in flowr.domain.session.
"""

from pathlib import Path
from typing import Protocol

from flowr.domain.session import Session


class SessionStore(Protocol):
    """Persistence interface for session state.

    Implementations must use atomic writes (temp-file-then-rename)
    to prevent partial state corruption.
    """

    def init(self, flow_name: str, name: str, flows_dir: Path) -> Session:
        """Create a new session at the flow's initial state.

        Args:
            flow_name: The flow name (resolved via FlowNameResolver).
            name: The session name (used as filename stem).
            flows_dir: The configured flows directory (for loading the flow).

        Returns:
            The newly created Session.

        Raises:
            SessionAlreadyExists: A session with this name already exists.
            FlowNotFound: The flow name cannot be resolved.
        """
        ...

    def load(self, name: str) -> Session:
        """Load a session by name.

        Args:
            name: The session name.

        Returns:
            The loaded Session.

        Raises:
            SessionNotFound: No session file exists for this name.
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


class SessionAlreadyExists(Exception):
    """Raised when attempting to init a session that already exists."""


class SessionNotFound(Exception):
    """Raised when a session file cannot be found."""


class SessionCorrupted(Exception):
    """Raised when a session YAML file cannot be parsed."""


class YamlSessionStore:
    """File-based session store using YAML with atomic writes.

    Sessions are stored as <name>.yaml in the configured sessions directory.
    Writes use temp-file-then-rename to prevent partial corruption.
    """

    def __init__(self, sessions_dir: Path) -> None:
        self._sessions_dir = sessions_dir

    def init(self, flow_name: str, name: str, flows_dir: Path) -> Session:
        """Create a new session at the flow's initial state."""
        raise NotImplementedError

    def load(self, name: str) -> Session:
        """Load a session from its YAML file."""
        raise NotImplementedError

    def save(self, session: Session) -> None:
        """Save a session using atomic write (write temp, then rename)."""
        raise NotImplementedError

    def list_sessions(self) -> list[Session]:
        """List all sessions, sorted by updated_at descending."""
        raise NotImplementedError