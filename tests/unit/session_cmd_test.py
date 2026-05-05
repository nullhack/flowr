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
    _cmd_states,
    _cmd_transition_session,
    _cmd_validate,
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


class TestSessionInitSubflowEntry:
    """Cover session_cmd.py:99-106 — auto-entry into subflow on init."""

    _PARENT_ENTRY = """\
flow: parent-entry
version: "1.0"
states:
  - id: start
    flow: sub.yaml
    next:
      done: end
  - id: end
    next: {}
"""

    _SUB_ENTRY = """\
flow: sub
version: "1.0"
exits: [done]
states:
  - id: sub-start
    next:
      finish: done
"""

    def test_init_auto_enters_subflow(self, tmp_path: Path) -> None:
        from flowr.cli.session_cmd import cmd_session_init

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "parent-entry.yaml").write_text(self._PARENT_ENTRY)
        (flows_dir / "sub.yaml").write_text(self._SUB_ENTRY)
        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()

        args = _ns(flow="parent-entry", name=None)
        rc = cmd_session_init(args, config, resolver)
        assert rc == 0

        store = YamlSessionStore(config.sessions_path())
        session = store.load("default")
        assert session.flow == "sub"
        assert session.state == "sub-start"
        assert len(session.stack) == 1
        assert session.stack[0].flow == "parent-entry"
        assert session.stack[0].state == "start"


class TestCmdValidateNoneGuard:
    """Cover __main__.py:242-243 — _cmd_validate flow_file None."""

    def test_validate_none_flow_file(self) -> None:
        args = _ns(flow_file=None, text_output=True)
        assert _cmd_validate(args) == 2


class TestCmdStatesNoneGuard:
    """Cover __main__.py:273-274 — _cmd_states flow_file None."""

    def test_states_none_flow_file(self) -> None:
        args = _ns(flow_file=None, text_output=True)
        assert _cmd_states(args) == 2


_GUARDED_FLOW = """\
flow: guarded-flow
version: "1.0"
states:
  - id: idle
    next:
      go:
        to: done
        when:
          score: ">=10"
  - id: done
    next: {}
"""


class TestBuildTransitionListBlocked:
    """Cover __main__.py:531 — blocked status branch."""

    def test_blocked_when_conditions_not_met(self, tmp_path: Path) -> None:
        from flowr.__main__ import _build_transition_list
        from flowr.domain.loader import load_flow_from_file

        path = _write_flow(tmp_path, _GUARDED_FLOW, "guarded.yaml")
        flow = load_flow_from_file(path)
        state = flow.states[0]

        transitions = _build_transition_list(state, {})
        assert len(transitions) == 1
        assert transitions[0]["status"] == "blocked"
        assert transitions[0]["conditions"] == {"score": ">=10"}


class TestFormatTransitionsTextBlocked:
    """Cover __main__.py:552-553 — condition hints when blocked."""

    def test_blocked_with_conditions_hint(self) -> None:
        from flowr.__main__ import _format_transitions_text

        transitions = [
            {
                "trigger": "go",
                "target": "done",
                "status": "blocked",
                "conditions": {"score": ">=10"},
            }
        ]
        result = _format_transitions_text("idle", transitions)
        assert "[blocked]" in result
        assert "need: score=>=10" in result


class TestDisplayPathValueError:
    """Cover __main__.py:591-592 — ValueError fallback in _display_path."""

    def test_unrelated_absolute_path(self) -> None:
        from flowr.__main__ import _display_path

        with patch.object(Path, "cwd", return_value=Path("/home/user/project")):
            result = _display_path(Path("/completely/unrelated/path"))
        assert result == "/completely/unrelated/path"


class TestFindFlowFile:
    """Cover __main__.py:635-638 — second attempt without .yaml + None return."""

    def test_not_found_returns_none(self, tmp_path: Path) -> None:
        from flowr.__main__ import _find_flow_file

        flows_dir = tmp_path / "flows"
        flows_dir.mkdir()
        assert _find_flow_file("nonexistent", flows_dir) is None

    def test_found_without_yaml_extension(self, tmp_path: Path) -> None:
        from flowr.__main__ import _find_flow_file

        flows_dir = tmp_path / "flows"
        flows_dir.mkdir()
        (flows_dir / "myflow").write_text("content")
        result = _find_flow_file("myflow", flows_dir)
        assert result == flows_dir / "myflow"


_FLOW_BAD_SUBFLOW_REF = """\
flow: parent-bad-ref
version: "1.0"
states:
  - id: idle
    next:
      go: work
  - id: work
    flow: nonexistent-child.yaml
    next:
      done: end
  - id: end
    next: {}
"""


class TestEnterSubflowNoneChild:
    """Cover __main__.py:662 — child is None guard in _enter_subflow."""

    def test_child_not_found_returns_none(self, tmp_path: Path) -> None:
        from flowr.__main__ import _enter_subflow
        from flowr.domain.loader import load_flow_from_file

        path = _write_flow(tmp_path, _FLOW_BAD_SUBFLOW_REF, "parent.yaml")
        flow = load_flow_from_file(path)
        session = Session(flow="parent-bad-ref", state="idle", name="test")
        result = _enter_subflow(session, flow, path, "work")
        assert result is None


_GRANDPARENT = """\
flow: grandparent
version: "1.0"
states:
  - id: idle
    next:
      go: work
  - id: work
    flow: child-nested.yaml
    next:
      done: end
  - id: end
    next: {}
"""

_CHILD_NESTED = """\
flow: child-nested
version: "1.0"
states:
  - id: child-start
    flow: grandchild.yaml
    next:
      finish: child-done
  - id: child-done
    next: {}
"""

_GRANDCHILD = """\
flow: grandchild
version: "1.0"
states:
  - id: gc-start
    next:
      step: gc-end
  - id: gc-end
    next: {}
"""


class TestEnterSubflowRecursiveGrandchild:
    """Cover __main__.py:671-679 — recursive grandchild entry."""

    def test_two_level_stack(self, tmp_path: Path) -> None:
        from flowr.__main__ import _enter_subflow
        from flowr.domain.loader import load_flow_from_file

        parent_path = _write_flow(tmp_path, _GRANDPARENT, "grandparent.yaml")
        _write_flow(tmp_path, _CHILD_NESTED, "child-nested.yaml")
        _write_flow(tmp_path, _GRANDCHILD, "grandchild.yaml")

        flow = load_flow_from_file(parent_path)
        session = Session(flow="grandparent", state="idle", name="test")
        result = _enter_subflow(session, flow, parent_path, "work")
        assert result is not None
        updated, display = result
        assert updated.flow == "grandchild"
        assert updated.state == "gc-start"
        assert len(updated.stack) == 2
        assert updated.stack[0] == SessionStackFrame(flow="grandparent", state="work")
        assert updated.stack[1] == SessionStackFrame(
            flow="child-nested", state="child-start"
        )
        assert display == "grandchild/gc-start"


class TestResolveSubflowExitFallbacks:
    """Cover __main__.py:699,704,708 — _resolve_subflow_exit fallback paths."""

    def test_parent_flow_file_not_found(self, tmp_path: Path) -> None:
        from flowr.__main__ import _resolve_subflow_exit

        flows_dir = tmp_path / "flows"
        flows_dir.mkdir()
        session = Session(
            flow="child",
            state="some-state",
            name="test",
            stack=[SessionStackFrame(flow="nonexistent-parent", state="review")],
        )
        updated, target = _resolve_subflow_exit(
            session, "trigger", "exit-name", flows_dir
        )
        assert target == "exit-name"
        assert len(updated.stack) == 0
        assert updated.flow == "nonexistent-parent"

    def test_parent_state_not_found(self, tmp_path: Path) -> None:
        from flowr.__main__ import _resolve_subflow_exit

        flows_dir = tmp_path / "flows"
        flows_dir.mkdir()
        # File name must match the stack frame's flow name for _find_flow_file
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        session = Session(
            flow="child",
            state="some-state",
            name="test",
            stack=[SessionStackFrame(flow="test-flow", state="nonexistent-state")],
        )
        updated, target = _resolve_subflow_exit(
            session, "trigger", "exit-name", flows_dir
        )
        assert target == "exit-name"
        assert len(updated.stack) == 0

    def test_parent_transition_not_found(self, tmp_path: Path) -> None:
        from flowr.__main__ import _resolve_subflow_exit

        flows_dir = tmp_path / "flows"
        flows_dir.mkdir()
        (flows_dir / "test-flow.yaml").write_text(_SIMPLE_FLOW)
        session = Session(
            flow="child",
            state="some-state",
            name="test",
            stack=[SessionStackFrame(flow="test-flow", state="idle")],
        )
        updated, target = _resolve_subflow_exit(
            session, "trigger", "nonexistent-exit", flows_dir
        )
        assert target == "nonexistent-exit"
        assert len(updated.stack) == 0


class TestCmdStatesSession:
    """Cover __main__.py:879-890 — _cmd_states_session."""

    def _setup(
        self, tmp_path: Path
    ) -> tuple[argparse.Namespace, FlowrConfig, DefaultFlowNameResolver]:
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
        return _ns(session="__default__", text_output=True), config, resolver

    def test_states_session_text(self, tmp_path: Path) -> None:
        from flowr.__main__ import _cmd_states_session

        args, config, resolver = self._setup(tmp_path)
        with pytest.raises(SystemExit) as exc_info:
            _cmd_states_session(args, config, resolver)
        assert exc_info.value.code == 0

    def test_states_session_json(self, tmp_path: Path) -> None:
        from flowr.__main__ import _cmd_states_session

        args, config, resolver = self._setup(tmp_path)
        args = _ns(session="__default__", text_output=False)
        with pytest.raises(SystemExit) as exc_info:
            _cmd_states_session(args, config, resolver)
        assert exc_info.value.code == 0


class TestCmdValidateSession:
    """Cover __main__.py:897-920 — _cmd_validate_session."""

    _VALID_FLOW = """\
flow: valid-flow
version: "1.0"
exits:
  - complete
states:
  - id: idle
    next:
      go: complete
"""

    def _setup(self, tmp_path: Path) -> tuple[FlowrConfig, DefaultFlowNameResolver]:
        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        (flows_dir / "valid-flow.yaml").write_text(self._VALID_FLOW)
        sessions_dir = tmp_path / ".flowr" / "sessions"
        sessions_dir.mkdir(parents=True)
        (sessions_dir / "default.yaml").write_text(
            yaml.dump(
                {
                    "flow": "valid-flow",
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
        config = FlowrConfig(
            flows_dir=config.flows_dir,
            sessions_dir=config.sessions_dir,
            default_flow="valid-flow",
            default_session=config.default_session,
            project_root=config.project_root,
        )
        return config, DefaultFlowNameResolver()

    def test_validate_session_text(self, tmp_path: Path) -> None:
        from flowr.__main__ import _cmd_validate_session

        config, resolver = self._setup(tmp_path)
        args = _ns(session="__default__", text_output=True)
        with pytest.raises(SystemExit) as exc_info:
            _cmd_validate_session(args, config, resolver)
        assert exc_info.value.code == 0

    def test_validate_session_json(self, tmp_path: Path) -> None:
        from flowr.__main__ import _cmd_validate_session

        config, resolver = self._setup(tmp_path)
        args = _ns(session="__default__", text_output=False)
        with pytest.raises(SystemExit) as exc_info:
            _cmd_validate_session(args, config, resolver)
        assert exc_info.value.code == 0

    def test_validate_session_with_violations(self, tmp_path: Path) -> None:
        """Cover line 909 — violation loop body."""
        from flowr.__main__ import _cmd_validate_session

        flows_dir = tmp_path / ".flowr" / "flows"
        flows_dir.mkdir(parents=True)
        # _SIMPLE_FLOW has no exits, so it will have violations
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
        args = _ns(session="__default__", text_output=False)
        with pytest.raises(SystemExit) as exc_info:
            _cmd_validate_session(args, config, resolver)
        assert exc_info.value.code == 1


class TestDispatchSessionCommandEdgeCases:
    """Cover __main__.py:965,968 — _dispatch_session_command edge cases."""

    def test_unknown_command_returns_false(self, tmp_path: Path) -> None:
        from flowr.__main__ import _dispatch_session_command

        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()
        args = _ns(session="__default__", command="mermaid")
        assert _dispatch_session_command(args, config, resolver) is False

    def test_no_session_returns_false(self, tmp_path: Path) -> None:
        from flowr.__main__ import _dispatch_session_command

        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()
        args = _ns(session=None, command="check")
        assert _dispatch_session_command(args, config, resolver) is False

    def test_valid_command_returns_true_after_handler(self, tmp_path: Path) -> None:
        from flowr.__main__ import _dispatch_session_command

        config = _config(tmp_path)
        resolver = DefaultFlowNameResolver()
        args = _ns(session="__default__", command="check")
        with patch("flowr.__main__._cmd_check_session"):
            result = _dispatch_session_command(args, config, resolver)
        assert result is True


class TestMainSessionDispatchReturn:
    """Cover __main__.py:992 — main() return after dispatch returns True."""

    def test_main_returns_after_session_dispatch(self, tmp_path: Path) -> None:
        from flowr.__main__ import main

        with (
            patch("sys.argv", ["flowr", "check", "--session"]),
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("flowr.__main__._dispatch_session_command", return_value=True),
        ):
            main()  # Should return, not raise SystemExit


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
