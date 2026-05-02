"""Unit tests for session store: init, load, save, resolve, list_sessions."""

from pathlib import Path

import pytest
import yaml

from flowr.domain.session import SessionStackFrame
from flowr.infrastructure.session_store import (
    SessionAlreadyExistsError,
    SessionCorruptedError,
    SessionNameNotFoundError,
    SessionNotFoundError,
    YamlSessionStore,
)

_SIMPLE_FLOW = """\
flow: test-flow
version: "1.0"
states:
  - id: idle
    next:
      go: done
  - id: done
"""


def _write_flow(flows_dir: Path, name: str = "test-flow.yaml") -> Path:
    flows_dir.mkdir(parents=True, exist_ok=True)
    p = flows_dir / name
    p.write_text(_SIMPLE_FLOW)
    return p


def _make_store(sessions_dir: Path) -> YamlSessionStore:
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return YamlSessionStore(sessions_dir)


class TestYamlSessionStoreInit:
    def test_init_creates_session(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / "flows"
        flow_path = _write_flow(flows_dir)
        store = _make_store(tmp_path / "sessions")

        session = store.init(flow_path, "default")

        assert session.flow == "test-flow"
        assert session.state == "idle"
        assert session.name == "default"
        assert (tmp_path / "sessions" / "default.yaml").exists()

    def test_init_rejects_duplicate(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / "flows"
        flow_path = _write_flow(flows_dir)
        store = _make_store(tmp_path / "sessions")
        store.init(flow_path, "default")

        with pytest.raises(SessionAlreadyExistsError):
            store.init(flow_path, "default")


class TestYamlSessionStoreLoad:
    def test_load_by_name(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / "flows"
        flow_path = _write_flow(flows_dir)
        store = _make_store(tmp_path / "sessions")
        store.init(flow_path, "my-session")

        session = store.load("my-session")
        assert session.name == "my-session"
        assert session.flow == "test-flow"

    def test_load_by_path(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / "flows"
        flow_path = _write_flow(flows_dir)
        store = _make_store(tmp_path / "sessions")
        store.init(flow_path, "default")

        session_path = tmp_path / "sessions" / "default.yaml"
        session = store.load(str(session_path))
        assert session.name == "default"

    def test_load_not_found_raises(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path / "sessions")

        with pytest.raises(SessionNotFoundError):
            store.load("nonexistent")

    def test_load_corrupted_raises(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "broken.yaml").write_text("{{invalid yaml")

        store = YamlSessionStore(sessions_dir)
        with pytest.raises(SessionCorruptedError):
            store.load("broken")

    def test_load_with_stack(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        data = {
            "flow": "sub-flow",
            "state": "sub-start",
            "name": "default",
            "created_at": "2026-01-01",
            "updated_at": "2026-01-02",
            "stack": [{"flow": "main-flow", "state": "middle"}],
            "params": {"key": {"nested": "val"}},
        }
        (sessions_dir / "default.yaml").write_text(yaml.dump(data))

        store = YamlSessionStore(sessions_dir)
        session = store.load("default")
        assert session.flow == "sub-flow"
        assert len(session.stack) == 1
        assert session.stack[0].flow == "main-flow"
        assert session.params == {"key": {"nested": "val"}}


class TestYamlSessionStoreResolve:
    def test_resolve_existing_file_path(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        session_path = sessions_dir / "my-session.yaml"
        session_path.write_text("flow: test")

        store = YamlSessionStore(sessions_dir)
        result = store.resolve(str(session_path))
        assert result == session_path

    def test_resolve_by_name(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "my-session.yaml").write_text("flow: test")

        store = YamlSessionStore(sessions_dir)
        result = store.resolve("my-session")
        assert result.name == "my-session.yaml"

    def test_resolve_by_name_with_yaml_extension(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "my-session.yaml").write_text("flow: test")

        store = YamlSessionStore(sessions_dir)
        result = store.resolve("my-session.yaml")
        assert result.name == "my-session.yaml"

    def test_resolve_not_found_raises(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        store = YamlSessionStore(sessions_dir)
        with pytest.raises(SessionNameNotFoundError) as exc_info:
            store.resolve("nonexistent")
        assert "nonexistent" in str(exc_info.value)


class TestYamlSessionStoreSave:
    def test_save_preserves_stack(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / "flows"
        flow_path = _write_flow(flows_dir)
        store = _make_store(tmp_path / "sessions")
        session = store.init(flow_path, "default")

        updated = session.push_stack(
            SessionStackFrame(flow="main-flow", state="middle"),
            "sub-start",
            new_flow="sub-flow",
        )
        store.save(updated)

        loaded = store.load("default")
        assert loaded.flow == "sub-flow"
        assert loaded.state == "sub-start"
        assert len(loaded.stack) == 1
        assert loaded.stack[0].flow == "main-flow"

    def test_save_atomic_write(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / "flows"
        flow_path = _write_flow(flows_dir)
        store = _make_store(tmp_path / "sessions")
        session = store.init(flow_path, "default")

        updated = session.with_state("done")
        store.save(updated)

        loaded = store.load("default")
        assert loaded.state == "done"


class TestYamlSessionStoreListSessions:
    def test_list_sessions_returns_all(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / "flows"
        flow_path = _write_flow(flows_dir)
        store = _make_store(tmp_path / "sessions")
        store.init(flow_path, "alpha")
        store.init(flow_path, "beta")

        sessions = store.list_sessions()
        names = [s.name for s in sessions]
        assert "alpha" in names
        assert "beta" in names

    def test_list_sessions_empty(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        store = YamlSessionStore(sessions_dir)

        sessions = store.list_sessions()
        assert sessions == []

    def test_list_sessions_skips_corrupted(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / "flows"
        flow_path = _write_flow(flows_dir)
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)
        store = YamlSessionStore(sessions_dir)
        store.init(flow_path, "good")
        (sessions_dir / "bad.yaml").write_text("{{invalid")

        sessions = store.list_sessions()
        names = [s.name for s in sessions]
        assert names == ["good"]
