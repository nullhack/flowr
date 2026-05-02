"""Session persistence: load/save session YAML files with atomic writes.

Implements the SessionStore Protocol defined in flowr.domain.session.
"""

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import yaml

from flowr.domain.loader import load_flow_from_file
from flowr.domain.session import Session, SessionStackFrame


class SessionAlreadyExistsError(Exception):
    """Raised when attempting to init a session that already exists."""


class SessionNotFoundError(Exception):
    """Raised when a session file cannot be found."""


class SessionCorruptedError(Exception):
    """Raised when a session YAML file cannot be parsed."""


class YamlSessionStore:
    """File-based session store using YAML with atomic writes.

    Sessions are stored as <name>.yaml in the configured sessions directory.
    Writes use temp-file-then-rename to prevent partial corruption.
    """

    def __init__(self, sessions_dir: Path) -> None:
        """Initialize with the sessions directory."""
        self._sessions_dir = sessions_dir

    def init(self, flow_path: Path, name: str) -> Session:
        """Create a new session at the flow's initial state.

        Returns:
            The newly created Session.

        Raises:
            SessionAlreadyExistsError: A session with this name already exists.
        """
        session_path = self._sessions_dir / f"{name}.yaml"
        if session_path.exists():
            msg = f"Session '{name}' already exists"
            raise SessionAlreadyExistsError(msg)

        flow = load_flow_from_file(flow_path)

        ts = datetime.now(tz=UTC).isoformat()
        session = Session(
            flow=flow.flow,
            state=flow.states[0].id,
            name=name,
            created_at=ts,
            updated_at=ts,
        )
        self.save(session)
        return session

    def load(self, name: str) -> Session:
        """Load a session from its YAML file.

        Returns:
            The loaded Session.

        Raises:
            SessionNotFoundError: No session file exists for this name.
            SessionCorruptedError: The session file contains invalid YAML.
        """
        session_path = self._sessions_dir / f"{name}.yaml"
        if not session_path.exists():
            msg = f"Session '{name}' not found"
            raise SessionNotFoundError(msg)
        try:
            data = yaml.safe_load(session_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            msg = f"Session '{name}' is corrupted: {exc}"
            raise SessionCorruptedError(msg) from exc

        stack = [
            SessionStackFrame(flow=f["flow"], state=f["state"])
            for f in data.get("stack", [])
        ]
        return Session(
            flow=data["flow"],
            state=data["state"],
            name=data.get("name", "default"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            stack=stack,
            params=data.get("params", {}),
        )

    def save(self, session: Session) -> None:
        """Save a session using atomic write (write temp, then rename)."""
        self._sessions_dir.mkdir(parents=True, exist_ok=True)
        session_path = self._sessions_dir / f"{session.name}.yaml"

        data = {
            "flow": session.flow,
            "state": session.state,
            "name": session.name,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "stack": [{"flow": f.flow, "state": f.state} for f in session.stack],
            "params": session.params,
        }

        fd, tmp_path = tempfile.mkstemp(dir=str(self._sessions_dir), suffix=".yaml")
        tmp = Path(tmp_path)
        try:
            os.close(fd)
            with tmp.open("w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False)
            tmp.replace(str(session_path))
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise

    def list_sessions(self) -> list[Session]:
        """List all sessions, sorted by updated_at descending."""
        raise NotImplementedError
