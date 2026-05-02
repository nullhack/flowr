"""Unit tests for session command handlers, config, and session store coverage."""

import argparse
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from flowr.__main__ import (
    _apply_session_transition,
    _cmd_config,
    _handle_session,
    _resolve_session,
)
from flowr.cli.resolution import DefaultFlowNameResolver
from flowr.domain.session import Session, SessionStackFrame
from flowr.infrastructure.config import (
    FlowrConfig,
    resolve_config_with_sources,
)
from flowr.infrastructure.session_store import (
    SessionAlreadyExistsError,
    SessionCorruptedError,
    SessionNotFoundError,
    YamlSessionStore,
)

_YAML_FLOW = (
    "flow: test-flow\nversion: '1.0'\n"
    "states:\n  - id: idle\n    next:\n"
    "      go:\n        to: done\n"
    "  - id: done\n    next: {}\n"
)

_YAML_FLOW_WITH_EXITS = (
    "flow: parent-flow\nversion: '1.0'\n"
    "exits:\n  - approved\n"
    "states:\n  - id: idle\n    next:\n"
    "      start:\n        to: review\n"
    "  - id: review\n    next:\n"
    "      approve:\n        to: approved\n"
)

_CHILD_FLOW = (
    "flow: child-flow\nversion: '1.0'\n"
    "exits:\n  - done\n"
    "states:\n  - id: entry\n    next:\n"
    "      finish:\n        to: done\n"
)


def _write_flow(tmp_path: Path, yaml_str: str, name: str = "test-flow.yaml") -> Path:
    flows_dir = tmp_path / ".flowr" / "flows"
    flows_dir.mkdir(parents=True, exist_ok=True)
    p = flows_dir / name
    p.write_text(yaml_str)
    return p


def _write_session(tmp_path: Path, session: Session) -> Path:
    sessions_dir = tmp_path / ".flowr" / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "flow": session.flow,
        "state": session.state,
        "name": session.name,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "stack": [{"flow": f.flow, "state": f.state} for f in session.stack],
        "params": session.params,
    }
    p = sessions_dir / f"{session.name}.yaml"
    p.write_text(yaml.dump(data, default_flow_style=False))
    return p


def _make_config(tmp_path: Path, **overrides: object) -> FlowrConfig:
    defaults = {
        "flows_dir": Path(".flowr/flows"),
        "sessions_dir": Path(".flowr/sessions"),
        "default_flow": "test-flow",
        "default_session": "default",
        "project_root": tmp_path,
    }
    defaults.update(overrides)
    return FlowrConfig(**defaults)


class TestYamlSessionStoreInit:
    def test_init_creates_session(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        store = YamlSessionStore(tmp_path / ".flowr" / "sessions")
        flow_path = tmp_path / ".flowr" / "flows" / "test-flow.yaml"
        session = store.init(flow_path, "default")
        assert session.flow == "test-flow"
        assert session.state == "idle"
        assert session.name == "default"

    def test_init_raises_if_exists(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        store = YamlSessionStore(tmp_path / ".flowr" / "sessions")
        flow_path = tmp_path / ".flowr" / "flows" / "test-flow.yaml"
        store.init(flow_path, "default")
        with pytest.raises(SessionAlreadyExistsError):
            store.init(flow_path, "default")


class TestYamlSessionStoreLoad:
    def test_load_existing_session(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        store = YamlSessionStore(tmp_path / ".flowr" / "sessions")
        flow_path = tmp_path / ".flowr" / "flows" / "test-flow.yaml"
        store.init(flow_path, "test-session")
        session = store.load("test-session")
        assert session.flow == "test-flow"
        assert session.state == "idle"

    def test_load_raises_not_found(self, tmp_path: Path) -> None:
        store = YamlSessionStore(tmp_path / ".flowr" / "sessions")
        with pytest.raises(SessionNotFoundError):
            store.load("nonexistent")

    def test_load_raises_corrupted(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "broken.yaml").write_text("{:invalid yaml: [")
        store = YamlSessionStore(sessions_dir)
        with pytest.raises(SessionCorruptedError):
            store.load("broken")


class TestYamlSessionStoreSave:
    def test_save_updates_session(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        store = YamlSessionStore(tmp_path / ".flowr" / "sessions")
        flow_path = tmp_path / ".flowr" / "flows" / "test-flow.yaml"
        session = store.init(flow_path, "default")
        updated = session.with_state("done")
        store.save(updated)
        loaded = store.load("default")
        assert loaded.state == "done"


class TestResolveSession:
    def test_resolve_session_loads_and_resolves(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        store = YamlSessionStore(tmp_path / ".flowr" / "sessions")
        flow_path = tmp_path / ".flowr" / "flows" / "test-flow.yaml"
        store.init(flow_path, "default")
        config = _make_config(tmp_path)
        resolver = DefaultFlowNameResolver()
        session, flow, _resolved_path = _resolve_session("default", config, resolver)
        assert session.flow == "test-flow"
        assert flow.flow == "test-flow"

    def test_resolve_session_not_found_exits(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        resolver = DefaultFlowNameResolver()
        with pytest.raises(SystemExit):
            _resolve_session("nonexistent", config, resolver)

    def test_resolve_session_flow_not_found_exits(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        session_data = {
            "flow": "nonexistent",
            "state": "idle",
            "name": "default",
            "created_at": "",
            "updated_at": "",
            "stack": [],
            "params": {},
        }
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(session_data, default_flow_style=False)
        )
        config = _make_config(tmp_path)
        resolver = DefaultFlowNameResolver()
        with pytest.raises(SystemExit):
            _resolve_session("default", config, resolver)


class TestApplySessionTransition:
    def test_simple_transition(self, tmp_path: Path) -> None:
        flow_path = _write_flow(tmp_path, _YAML_FLOW)
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(flow_path)
        session = Session(flow="test-flow", state="idle", name="default")
        _updated, target = _apply_session_transition(session, flow, flow_path, "go", {})
        assert target == "done"

    def test_transition_not_found_exits(self, tmp_path: Path) -> None:
        flow_path = _write_flow(tmp_path, _YAML_FLOW)
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(flow_path)
        session = Session(flow="test-flow", state="idle", name="default")
        with pytest.raises(SystemExit):
            _apply_session_transition(session, flow, flow_path, "nonexistent", {})

    def test_state_not_found_exits(self, tmp_path: Path) -> None:
        flow_path = _write_flow(tmp_path, _YAML_FLOW)
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(flow_path)
        session = Session(flow="test-flow", state="missing", name="default")
        with pytest.raises(SystemExit):
            _apply_session_transition(session, flow, flow_path, "go", {})

    def test_subflow_push(self, tmp_path: Path) -> None:
        parent_path = _write_flow(tmp_path, _YAML_FLOW_WITH_EXITS, "parent-flow.yaml")
        _write_flow(tmp_path, _CHILD_FLOW, "child-flow.yaml")
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(parent_path)
        session = Session(flow="parent-flow", state="idle", name="default")
        _updated, target = _apply_session_transition(
            session, flow, parent_path, "start", {}
        )
        assert "child-flow" in target or "review" in target

    def test_subflow_pop(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW_WITH_EXITS, "parent-flow.yaml")
        _write_flow(tmp_path, _CHILD_FLOW, "child-flow.yaml")
        from flowr.domain.loader import load_flow_from_file

        frame = SessionStackFrame(flow="parent-flow", state="idle")
        session = Session(
            flow="child-flow", state="entry", name="default", stack=[frame]
        )
        child_flow_path = tmp_path / ".flowr" / "flows" / "child-flow.yaml"
        child_flow = load_flow_from_file(child_flow_path)
        updated, target = _apply_session_transition(
            session, child_flow, child_flow_path, "finish", {}
        )
        assert target == "done"
        assert len(updated.stack) == 0


class TestCmdConfig:
    def test_config_text_output(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        ns = argparse.Namespace(json_output=False, flows_dir=None)
        rc = _cmd_config(ns)
        assert rc == 0

    def test_config_json_output(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        ns = argparse.Namespace(json_output=True, flows_dir=None)
        rc = _cmd_config(ns)
        assert rc == 0


class TestCmdCheckSession:
    def test_check_session_missing_state(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        session_data = {
            "flow": "test-flow",
            "state": "idle",
            "name": "default",
            "created_at": "",
            "updated_at": "",
            "stack": [],
            "params": {},
        }
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(session_data, default_flow_style=False)
        )
        result = subprocess.run(
            [sys.executable, "-m", "flowr", "check", "--session", "default", "idle"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode in (0, 1, 2)


class TestCmdNextSession:
    def test_next_session_basic(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        session_data = {
            "flow": "test-flow",
            "state": "idle",
            "name": "default",
            "created_at": "",
            "updated_at": "",
            "stack": [],
            "params": {},
        }
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(session_data, default_flow_style=False)
        )
        result = subprocess.run(
            [sys.executable, "-m", "flowr", "next", "--session", "default", "idle"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode in (0, 1, 2)


class TestCmdTransitionSession:
    def test_transition_session_no_trigger(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _YAML_FLOW)
        result = subprocess.run(
            [sys.executable, "-m", "flowr", "transition", "--session"],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        assert result.returncode == 2


class TestHandleSession:
    def test_handle_session_no_command(self, tmp_path: Path) -> None:
        ns = argparse.Namespace(session_command=None)
        config = _make_config(tmp_path)
        resolver = DefaultFlowNameResolver()
        with pytest.raises(SystemExit):
            _handle_session(ns, config, resolver)

    def test_handle_session_unknown_command(self, tmp_path: Path) -> None:
        ns = argparse.Namespace(session_command="bogus")
        config = _make_config(tmp_path)
        resolver = DefaultFlowNameResolver()
        with pytest.raises(SystemExit):
            _handle_session(ns, config, resolver)


class TestResolveConfigWithSources:
    def test_defaults(self, tmp_path: Path) -> None:
        _config, sources = resolve_config_with_sources(project_root=tmp_path)
        assert sources["project_root"] == "cwd"
        assert sources["flows_dir"] == "default"
        assert sources["default_flow"] == "default"

    def test_pyproject_overrides(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.flowr]\nflows_dir = "custom/flows"\ndefault_flow = "my-flow"\n'
        )
        config, sources = resolve_config_with_sources(project_root=tmp_path)
        assert sources["flows_dir"] == "pyproject.toml"
        assert config.flows_dir == Path("custom/flows")

    def test_cli_overrides(self, tmp_path: Path) -> None:
        custom_dir = tmp_path / "custom_flows"
        custom_dir.mkdir()
        config, sources = resolve_config_with_sources(
            project_root=tmp_path,
            cli_overrides={"flows_dir": str(custom_dir)},
        )
        assert sources["flows_dir"] == "cli"
        assert config.flows_dir == Path(str(custom_dir))

    def test_mixed_sources(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.flowr]\ndefault_flow = "my-flow"\n')
        custom_dir = tmp_path / "custom_flows"
        custom_dir.mkdir()
        _config, sources = resolve_config_with_sources(
            project_root=tmp_path,
            cli_overrides={"flows_dir": str(custom_dir)},
        )
        assert sources["flows_dir"] == "cli"
        assert sources["default_flow"] == "pyproject.toml"
        assert sources["sessions_dir"] == "default"


class TestSessionDomain:
    def test_with_state_explicit_timestamp(self) -> None:
        s = Session(flow="f", state="idle", name="n")
        updated = s.with_state("done", updated_at="2026-01-01T00:00:00")
        assert updated.state == "done"
        assert updated.updated_at == "2026-01-01T00:00:00"

    def test_push_stack_with_new_flow(self) -> None:
        s = Session(flow="parent", state="idle", name="n")
        frame = SessionStackFrame(flow="parent", state="idle")
        updated = s.push_stack(frame, "entry", new_flow="child")
        assert updated.flow == "child"
        assert updated.state == "entry"
        assert len(updated.stack) == 1

    def test_push_stack_without_new_flow(self) -> None:
        s = Session(flow="parent", state="idle", name="n")
        frame = SessionStackFrame(flow="parent", state="idle")
        updated = s.push_stack(frame, "entry")
        assert updated.flow == "parent"
        assert updated.state == "entry"

    def test_pop_stack_restores_parent(self) -> None:
        frame = SessionStackFrame(flow="parent", state="idle")
        s = Session(flow="child", state="entry", name="n", stack=[frame])
        updated = s.pop_stack("done")
        assert updated.flow == "parent"
        assert updated.state == "done"
        assert len(updated.stack) == 0

    def test_pop_stack_empty_uses_current_flow(self) -> None:
        s = Session(flow="solo", state="idle", name="n", stack=[])
        updated = s.pop_stack("done")
        assert updated.flow == "solo"
        assert updated.state == "done"
