"""Unit tests for session command handlers and session-aware CLI dispatch."""

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from flowr.__main__ import (
    _apply_session_transition,
    _cmd_check,
    _cmd_check_session,
    _cmd_config,
    _cmd_next,
    _cmd_next_session,
    _cmd_transition_session,
    _resolve_flow_for_command,
    _resolve_session,
)
from flowr.cli.resolution import DefaultFlowNameResolver
from flowr.domain.session import Session, SessionStackFrame
from flowr.infrastructure.config import FlowrConfig
from flowr.infrastructure.session_store import (
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
    next: {}
"""

_SUBFLOW_FLOW = """\
flow: parent-flow
version: "1.0"
exits:
  - done
states:
  - id: idle
    next:
      start: review
  - id: review
    flow: child.yaml
    next:
      done: complete
  - id: complete
    next: {}
"""

_CHILD_FLOW = """\
flow: child
version: "1.0"
exits:
  - approved
states:
  - id: entry
    next:
      approve: approved
  - id: approved
    next: {}
"""


def _write_flow(tmp_path: Path, yaml_str: str, name: str = "flow.yaml") -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml_str)
    return p


def _ns(**kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _config(tmp_path: Path) -> FlowrConfig:
    return FlowrConfig(
        flows_dir=Path(".flowr/flows"),
        sessions_dir=Path(".flowr/sessions"),
        default_flow="test-flow",
        default_session="default",
        project_root=tmp_path,
    )


class TestCmdSessionInit:
    def test_init_creates_session(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_init

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(flow="test-flow", name=None)
        rc = cmd_session_init(args, config, resolver)
        assert rc == 0
        assert (tmp_path / ".flowr" / "sessions" / "default.yaml").exists()

    def test_init_rejects_duplicate(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_init

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(flow="test-flow", name=None)
        cmd_session_init(args, config, resolver)

        with pytest.raises(SystemExit) as exc_info:
            cmd_session_init(args, config, resolver)
        assert exc_info.value.code == 1

    def test_init_flow_not_found(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_init

        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(flow="nonexistent-flow", name=None)
        with pytest.raises(SystemExit) as exc_info:
            cmd_session_init(args, config, resolver)
        assert exc_info.value.code == 1


class TestCmdSessionShow:
    def test_show_displays_session(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_show

        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(name=None, output_format="yaml")
        rc = cmd_session_show(args, config, resolver)
        assert rc == 0

    def test_show_json_format(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_show

        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(name=None, output_format="json")
        rc = cmd_session_show(args, config, resolver)
        assert rc == 0

    def test_show_not_found(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_show

        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(name="nonexistent", output_format="yaml")
        with pytest.raises(SystemExit) as exc_info:
            cmd_session_show(args, config, resolver)
        assert exc_info.value.code == 1


class TestCmdSessionSetState:
    def test_set_state_updates_state(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_set_state

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(state="done", name=None)
        rc = cmd_session_set_state(args, config, resolver)
        assert rc == 0

        data = yaml.safe_load((sessions_dir / "default.yaml").read_text())
        assert data["state"] == "done"

    def test_set_state_rejects_invalid_state(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_set_state

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(state="nonexistent", name=None)
        with pytest.raises(SystemExit) as exc_info:
            cmd_session_set_state(args, config, resolver)
        assert exc_info.value.code == 1

    def test_set_state_not_found_session(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_set_state

        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(state="idle", name="nonexistent")
        with pytest.raises(SystemExit) as exc_info:
            cmd_session_set_state(args, config, resolver)
        assert exc_info.value.code == 1


class TestCmdSessionList:
    def test_list_returns_sessions(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_list

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        store = YamlSessionStore(config.sessions_path())
        store.init(config.flows_path() / "test-flow.yaml", "alpha")
        store.init(config.flows_path() / "test-flow.yaml", "beta")

        args = _ns(output_format="yaml")
        rc = cmd_session_list(args, config, resolver)
        assert rc == 0

    def test_list_json_format(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_list

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        store = YamlSessionStore(config.sessions_path())
        store.init(config.flows_path() / "test-flow.yaml", "default")

        args = _ns(output_format="json")
        rc = cmd_session_list(args, config, resolver)
        assert rc == 0


class TestResolveSession:
    def test_resolve_session_loads_and_resolves(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        session, flow, _flow_path = _resolve_session("default", config, resolver)
        assert session.flow == "test-flow"
        assert session.state == "idle"
        assert flow.flow == "test-flow"

    def test_resolve_session_not_found(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        with pytest.raises(SystemExit) as exc_info:
            _resolve_session("nonexistent", config, resolver)
        assert exc_info.value.code == 1


class TestApplySessionTransition:
    def test_simple_state_transition(self, tmp_path: Path) -> None:
        flow_path = _write_flow(tmp_path, _SIMPLE_FLOW, "test-flow.yaml")
        DefaultFlowNameResolver()
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(flow_path)
        session = Session(flow="test-flow", state="idle", name="default")
        updated, target = _apply_session_transition(session, flow, flow_path, "go", {})
        assert updated.state == "done"
        assert target == "done"

    def test_subflow_push(self, tmp_path: Path) -> None:
        parent_path = _write_flow(tmp_path, _SUBFLOW_FLOW, "parent-flow.yaml")
        _write_flow(tmp_path, _CHILD_FLOW, "child.yaml")
        DefaultFlowNameResolver()
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(parent_path)
        session = Session(flow="parent-flow", state="idle", name="default")
        updated, _target = _apply_session_transition(
            session, flow, parent_path, "start", {}
        )
        assert updated.flow == "child"
        assert updated.state == "entry"
        assert len(updated.stack) == 1
        assert updated.stack[0].flow == "parent-flow"

    def test_subflow_pop(self, tmp_path: Path) -> None:
        _write_flow(tmp_path, _SUBFLOW_FLOW, "parent-flow.yaml")
        child_path = _write_flow(tmp_path, _CHILD_FLOW, "child.yaml")
        from flowr.domain.loader import load_flow_from_file

        child_flow = load_flow_from_file(child_path)
        session = Session(
            flow="child",
            state="entry",
            name="default",
            stack=[SessionStackFrame(flow="parent-flow", state="review")],
        )
        updated, _target = _apply_session_transition(
            session, child_flow, child_path, "approve", {}
        )
        assert updated.flow == "parent-flow"
        assert updated.state == "approved"
        assert len(updated.stack) == 0

    def test_invalid_trigger(self, tmp_path: Path) -> None:
        flow_path = _write_flow(tmp_path, _SIMPLE_FLOW, "test-flow.yaml")
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(flow_path)
        session = Session(flow="test-flow", state="idle", name="default")

        with pytest.raises(SystemExit) as exc_info:
            _apply_session_transition(session, flow, flow_path, "nonexistent", {})
        assert exc_info.value.code == 1


class TestCmdConfig:
    def test_config_text_output(self, tmp_path: Path) -> None:
        args = _ns(text_output=True, flows_dir=None)
        rc = _cmd_config(args)
        assert rc == 0

    def test_config_json_output(self, tmp_path: Path) -> None:
        args = _ns(text_output=False, flows_dir=None)
        rc = _cmd_config(args)
        assert rc == 0

    def test_config_with_flows_dir_override(self, tmp_path: Path) -> None:
        args = _ns(text_output=True, flows_dir="/custom/flows")
        rc = _cmd_config(args)
        assert rc == 0


class TestCheckSessionAndNextSession:
    def test_check_session_reads_state(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            session="__default__",
            text_output=True,
            target=None,
            evidence=[],
            evidence_json=None,
        )
        with pytest.raises(SystemExit) as exc_info:
            _cmd_check_session(args, config, resolver)
        assert exc_info.value.code == 0

    def test_next_session_shows_transitions(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            session="__default__", text_output=True, evidence=[], evidence_json=None
        )
        with pytest.raises(SystemExit) as exc_info:
            _cmd_next_session(args, config, resolver)
        assert exc_info.value.code == 0


class TestTransitionSession:
    def test_transition_session_updates_state(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            session="__default__",
            positional=["go"],
            text_output=True,
            evidence=[],
            evidence_json=None,
        )
        with pytest.raises(SystemExit) as exc_info:
            _cmd_transition_session(args, config, resolver)
        assert exc_info.value.code == 0

        data = yaml.safe_load((sessions_dir / "default.yaml").read_text())
        assert data["state"] == "done"

    def test_transition_session_missing_trigger(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            session="__default__",
            positional=[],
            text_output=True,
            evidence=[],
            evidence_json=None,
        )
        with pytest.raises(SystemExit) as exc_info:
            _cmd_transition_session(args, config, resolver)
        assert exc_info.value.code == 2


class TestResolveFlowForCommand:
    def test_resolve_for_check(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            command="check",
            flow_file="test-flow",
            state_id="idle",
            positional=None,
        )
        _resolve_flow_for_command(args, config, resolver)
        assert args.flow_file.exists()

    def test_resolve_for_transition(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            command="transition",
            positional=["test-flow", "idle", "go"],
        )
        _resolve_flow_for_command(args, config, resolver)
        assert args.flow_file.exists()

    def test_resolve_transition_missing_args(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(command="transition", positional=["test-flow"])
        with pytest.raises(SystemExit) as exc_info:
            _resolve_flow_for_command(args, config, resolver)
        assert exc_info.value.code == 2


class TestCheckNextWithoutSession:
    def test_check_missing_flow_file(self, tmp_path: Path) -> None:
        args = _ns(
            flow_file=None, state_id=None, target=None, text_output=True, session=None
        )
        rc = _cmd_check(args)
        assert rc == 2

    def test_check_missing_state_id(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            flow_file=resolver.resolve("test-flow", config.flows_path()),
            state_id=None,
            target=None,
            text_output=True,
            session=None,
        )
        rc = _cmd_check(args)
        assert rc == 2

    def test_check_state_not_found(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            flow_file=resolver.resolve("test-flow", config.flows_path()),
            state_id="nonexistent",
            target=None,
            text_output=True,
            session=None,
        )
        rc = _cmd_check(args)
        assert rc == 1

    def test_next_missing_state_id(self, tmp_path: Path) -> None:
        args = _ns(
            flow_file=None,
            state_id=None,
            text_output=True,
            evidence=[],
            evidence_json=None,
            session=None,
        )
        rc = _cmd_next(args)
        assert rc == 2

    def test_transition_with_positional_args(self, tmp_path: Path) -> None:
        from flowr.__main__ import _cmd_transition

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            flow_file=resolver.resolve("test-flow", config.flows_path()),
            positional=["test-flow", "idle", "go"],
            state_id=None,
            trigger=None,
            text_output=True,
            evidence=[],
            evidence_json=None,
        )
        rc = _cmd_transition(args)
        assert rc == 0

    def test_transition_trigger_not_found(self, tmp_path: Path) -> None:
        from flowr.__main__ import _cmd_transition

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            flow_file=resolver.resolve("test-flow", config.flows_path()),
            positional=None,
            state_id="idle",
            trigger="nonexistent",
            text_output=True,
            evidence=[],
            evidence_json=None,
        )
        rc = _cmd_transition(args)
        assert rc == 1


class TestMainDispatch:
    def test_session_command_dispatches(self, tmp_path: Path) -> None:
        from flowr.__main__ import main

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        config = _config(tmp_path)
        DefaultFlowNameResolver()

        store = YamlSessionStore(config.sessions_path())
        store.init(config.flows_path() / "test-flow.yaml", "default")

        with (
            patch("sys.argv", ["flowr", "session", "show", "--format", "yaml"]),
            patch.object(Path, "cwd", return_value=tmp_path),
            pytest.raises(SystemExit),
        ):
            main()

    def test_config_command_dispatches(self, tmp_path: Path) -> None:
        from flowr.__main__ import main

        with (
            patch("sys.argv", ["flowr", "config"]),
            patch.object(Path, "cwd", return_value=tmp_path),
            pytest.raises(SystemExit),
        ):
            main()

    def test_check_with_session_dispatches(self, tmp_path: Path) -> None:
        from flowr.__main__ import main

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )

        with (
            patch("sys.argv", ["flowr", "check", "--session"]),
            patch.object(Path, "cwd", return_value=tmp_path),
            pytest.raises(SystemExit),
        ):
            main()

    def test_next_with_session_dispatches(self, tmp_path: Path) -> None:
        from flowr.__main__ import main

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )

        with (
            patch("sys.argv", ["flowr", "next", "--session"]),
            patch.object(Path, "cwd", return_value=tmp_path),
            pytest.raises(SystemExit),
        ):
            main()

    def test_transition_with_session_dispatches(self, tmp_path: Path) -> None:
        from flowr.__main__ import main

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )

        with (
            patch("sys.argv", ["flowr", "transition", "go", "--session"]),
            patch.object(Path, "cwd", return_value=tmp_path),
            pytest.raises(SystemExit),
        ):
            main()

    def test_resolve_flow_not_found_for_command(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(command="check", flow_file="nonexistent", state_id="idle")
        with pytest.raises(SystemExit) as exc_info:
            _resolve_flow_for_command(args, config, resolver)
        assert exc_info.value.code == 1


class TestCmdSessionSetStateFlowNotFound:
    def test_set_state_flow_not_found(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_set_state

        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "nonexistent-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(state="done", name=None)
        with pytest.raises(SystemExit) as exc_info:
            cmd_session_set_state(args, config, resolver)
        assert exc_info.value.code == 1


class TestCheckSessionWithTarget:
    def test_check_session_with_target(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(session="__default__", text_output=True, target="done")
        with pytest.raises(SystemExit) as exc_info:
            _cmd_check_session(args, config, resolver)
        assert exc_info.value.code == 1

    def test_check_session_state_not_found(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "nonexistent",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(session="__default__", text_output=True, target=None)
        with pytest.raises(SystemExit) as exc_info:
            _cmd_check_session(args, config, resolver)
        assert exc_info.value.code == 1


class TestNextSessionJson:
    def test_next_session_json_output(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            session="__default__", text_output=False, evidence=[], evidence_json=None
        )
        with pytest.raises(SystemExit) as exc_info:
            _cmd_next_session(args, config, resolver)
        assert exc_info.value.code == 0


class TestTransitionSessionJson:
    def test_transition_json_output(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            session="__default__",
            positional=["go"],
            text_output=False,
            evidence=[],
            evidence_json=None,
        )
        with pytest.raises(SystemExit) as exc_info:
            _cmd_transition_session(args, config, resolver)
        assert exc_info.value.code == 0


class TestApplySessionTransitionEdgeCases:
    def test_state_not_found_in_session(self, tmp_path: Path) -> None:
        flow_path = _write_flow(tmp_path, _SIMPLE_FLOW, "test-flow.yaml")
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(flow_path)
        session = Session(flow="test-flow", state="nonexistent", name="default")

        with pytest.raises(SystemExit) as exc_info:
            _apply_session_transition(session, flow, flow_path, "go", {})
        assert exc_info.value.code == 1


class TestResolveSessionFlowNotFound:
    def test_resolve_session_flow_not_found(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "nonexistent-flow",
                    "state": "idle",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        with pytest.raises(SystemExit) as exc_info:
            _resolve_session("default", config, resolver)
        assert exc_info.value.code == 1


class TestCmdNextMissingStateId:
    def test_next_missing_state_id(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        flow_file = resolver.resolve("test-flow", config.flows_path())
        args = _ns(
            flow_file=flow_file,
            state_id=None,
            text_output=True,
            evidence=[],
            evidence_json=None,
            session=None,
        )
        rc = _cmd_next(args)
        assert rc == 2


class TestHandleSessionDispatch:
    def test_handle_session_unknown_command(self, tmp_path: Path) -> None:
        from flowr.__main__ import _handle_session

        args = _ns(session_command="unknown", session=None)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        with pytest.raises(SystemExit) as exc_info:
            _handle_session(args, config, resolver)
        assert exc_info.value.code == 2


class TestNextSessionStateNotFound:
    def test_next_session_state_not_found(self, tmp_path: Path) -> None:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "test-flow",
                    "state": "nonexistent",
                    "name": "default",
                    "created_at": "2026-01-01",
                    "updated_at": "2026-01-01",
                    "stack": [],
                    "params": {},
                }
            )
        )
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(
            session="__default__", text_output=True, evidence=[], evidence_json=None
        )
        with pytest.raises(SystemExit) as exc_info:
            _cmd_next_session(args, config, resolver)
        assert exc_info.value.code == 1


class TestResolveFlowForCommandNotFound:
    def test_resolve_flow_not_found_for_check(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(command="check", flow_file="nonexistent", state_id="idle")
        with pytest.raises(SystemExit) as exc_info:
            _resolve_flow_for_command(args, config, resolver)
        assert exc_info.value.code == 1

    def test_resolve_flow_not_found_for_transition(self, tmp_path: Path) -> None:
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(command="transition", positional=["nonexistent", "idle", "go"])
        with pytest.raises(SystemExit) as exc_info:
            _resolve_flow_for_command(args, config, resolver)
        assert exc_info.value.code == 1


class TestApplySessionTransitionSimpleElse:
    def test_simple_transition_else_branch(self, tmp_path: Path) -> None:
        flow_path = _write_flow(tmp_path, _SIMPLE_FLOW, "test-flow.yaml")
        from flowr.domain.loader import load_flow_from_file

        flow = load_flow_from_file(flow_path)
        session = Session(flow="test-flow", state="idle", name="default")
        updated, target = _apply_session_transition(session, flow, flow_path, "go", {})
        assert updated.state == "done"
        assert target == "done"
        assert updated.flow == "test-flow"


_CHAIN_PARENT = """\
flow: chain-parent
version: "1.0"
exits:
  - done
states:
  - id: step-1
    flow: chain-child-a
    next:
      complete: step-2
  - id: step-2
    flow: chain-child-b
    next:
      complete: done
  - id: done
    next: {}
"""

_CHAIN_CHILD_A = """\
flow: chain-child-a
version: "1.0"
exits:
  - complete
states:
  - id: a-start
    next:
      finish: complete
"""

_CHAIN_CHILD_B = """\
flow: chain-child-b
version: "1.0"
exits:
  - complete
states:
  - id: b-start
    next:
      finish: complete
"""


class TestSubflowExitResolution:
    def test_exit_resolves_parent_transition(self, tmp_path: Path) -> None:
        from flowr.domain.loader import load_flow_from_file

        parent = """\
flow: simple-parent
version: "1.0"
states:
  - id: step-1
    flow: simple-child
    next:
      complete: step-2
  - id: step-2
    next: {}
"""
        child = """\
flow: simple-child
version: "1.0"
exits:
  - complete
states:
  - id: child-start
    next:
      finish: complete
"""
        _write_flow(tmp_path, parent, "simple-parent.yaml")
        _write_flow(tmp_path, child, "simple-child.yaml")
        child_path = tmp_path / "simple-child.yaml"

        child_flow = load_flow_from_file(child_path)
        session = Session(
            flow="simple-child",
            state="child-start",
            name="test",
            stack=[SessionStackFrame(flow="simple-parent", state="step-1")],
        )
        updated, target = _apply_session_transition(
            session,
            child_flow,
            child_path,
            "finish",
            {},
            flows_dir=tmp_path,
        )
        assert updated.flow == "simple-parent"
        assert updated.state == "step-2"
        assert len(updated.stack) == 0
        assert target == "step-2"

    def test_exit_chains_into_next_subflow(self, tmp_path: Path) -> None:
        from flowr.domain.loader import load_flow_from_file

        _write_flow(tmp_path, _CHAIN_PARENT, "chain-parent.yaml")
        _write_flow(tmp_path, _CHAIN_CHILD_A, "chain-child-a.yaml")
        _write_flow(tmp_path, _CHAIN_CHILD_B, "chain-child-b.yaml")
        child_a_path = tmp_path / "chain-child-a.yaml"

        child_a = load_flow_from_file(child_a_path)
        session = Session(
            flow="chain-child-a",
            state="a-start",
            name="test",
            stack=[SessionStackFrame(flow="chain-parent", state="step-1")],
        )
        updated, target = _apply_session_transition(
            session,
            child_a,
            child_a_path,
            "finish",
            {},
            flows_dir=tmp_path,
        )
        assert updated.flow == "chain-child-b"
        assert updated.state == "b-start"
        assert len(updated.stack) == 1
        assert updated.stack[0].flow == "chain-parent"
        assert updated.stack[0].state == "step-2"
        assert target == "chain-child-b/b-start"

    def test_exit_without_flows_dir_uses_exit_name(self, tmp_path: Path) -> None:
        from flowr.domain.loader import load_flow_from_file

        _write_flow(tmp_path, _CHAIN_CHILD_A, "chain-child-a.yaml")
        child_a_path = tmp_path / "chain-child-a.yaml"

        child_a = load_flow_from_file(child_a_path)
        session = Session(
            flow="chain-child-a",
            state="a-start",
            name="test",
            stack=[SessionStackFrame(flow="chain-parent", state="step-1")],
        )
        updated, target = _apply_session_transition(
            session,
            child_a,
            child_a_path,
            "finish",
            {},
        )
        assert updated.flow == "chain-parent"
        assert updated.state == "complete"
        assert target == "complete"

    def test_subflow_push_without_extension(self, tmp_path: Path) -> None:
        from flowr.domain.loader import load_flow_from_file

        parent = """\
flow: no-ext-parent
version: "1.0"
states:
  - id: idle
    next:
      go: work
  - id: work
    flow: no-ext-child
    next:
      done: end
  - id: end
    next: {}
"""
        child = """\
flow: no-ext-child
version: "1.0"
exits: [done]
states:
  - id: child-start
    next:
      finish: done
"""
        _write_flow(tmp_path, parent, "no-ext-parent.yaml")
        _write_flow(tmp_path, child, "no-ext-child.yaml")

        parent_path = tmp_path / "no-ext-parent.yaml"
        parent_flow = load_flow_from_file(parent_path)
        session = Session(flow="no-ext-parent", state="idle", name="test")
        updated, _target = _apply_session_transition(
            session, parent_flow, parent_path, "go", {}
        )
        assert updated.flow == "no-ext-child"
        assert updated.state == "child-start"
        assert len(updated.stack) == 1
