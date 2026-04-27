"""Unit tests for CLI command functions — in-process coverage."""

import argparse
from pathlib import Path
from unittest.mock import patch

import pytest

from flowr.__main__ import (
    _cmd_check,
    _cmd_mermaid,
    _cmd_next,
    _cmd_states,
    _cmd_transition,
    _cmd_validate,
    _conditions_met,
    _find_passing_transitions,
    _find_state,
    _parse_evidence,
    main,
)
from flowr.domain.flow_definition import (
    Flow,
    GuardCondition,
    State,
    Transition,
)


def _write_flow(tmp_path: Path, yaml_str: str, name: str = "flow.yaml") -> Path:
    p = tmp_path / name
    p.write_text(yaml_str)
    return p


def _ns(**kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


_SIMPLE_YAML = (
    "flow: test\nversion: '1.0'\nexits:\n  - exit_done\n"
    "states:\n  - id: idle\n    next:\n"
    "      go:\n        to: done\n"
    "  - id: done\n    next: {}\n"
)

_GUARDED_YAML = (
    "flow: test\nversion: '1.0'\nexits:\n  - exit_done\n"
    "states:\n  - id: idle\n    next:\n"
    "      go:\n        to: done\n"
    "        when:\n          score: '>=80'\n"
    "  - id: done\n    next: {}\n"
)

_ATTRS_YAML = (
    "flow: test\nversion: '1.0'\nexits:\n  - exit_done\n"
    "attrs:\n  color: blue\n"
    "states:\n  - id: idle\n    attrs:\n      size: 1\n"
    "    next:\n      go:\n        to: done\n"
    "  - id: done\n    next: {}\n"
)

_SUBFLOW_YAML = (
    "flow: parent\nversion: '1.0'\nexits:\n  - complete\n"
    "states:\n  - id: idle\n    next:\n"
    "      start:\n        to: review\n"
    "  - id: review\n    flow: child.yaml\n"
    "    next:\n      done:\n        to: complete\n"
)

_CHILD_YAML = (
    "flow: child\nversion: '1.0'\nexits:\n  - approved\n"
    "states:\n  - id: entry\n    next:\n"
    "      approve:\n        to: approved\n"
)


class TestFindState:
    def test_find_existing_state(self) -> None:
        flow = Flow(
            flow="t",
            version="1.0",
            exits=["done"],
            states=[State(id="idle", next={})],
            params=[],
        )
        result = _find_state(flow, "idle")
        assert result is not None
        assert result.id == "idle"

    def test_find_missing_state(self) -> None:
        flow = Flow(
            flow="t",
            version="1.0",
            exits=["done"],
            states=[State(id="idle", next={})],
            params=[],
        )
        assert _find_state(flow, "missing") is None


class TestParseEvidence:
    def test_key_value_pairs(self) -> None:
        ns = _ns(evidence=["score=80", "name=alice"], evidence_json=None)
        result = _parse_evidence(ns)
        assert result == {"score": "80", "name": "alice"}

    def test_json_evidence(self) -> None:
        ns = _ns(evidence=[], evidence_json='{"score": 80, "name": "alice"}')
        result = _parse_evidence(ns)
        assert result == {"score": "80", "name": "alice"}

    def test_empty_evidence(self) -> None:
        ns = _ns(evidence=[], evidence_json=None)
        result = _parse_evidence(ns)
        assert result == {}


class TestFindPassingTransitions:
    def test_unguarded_passes(self) -> None:
        state = State(
            id="idle",
            next={"go": Transition(trigger="go", target="done")},
        )
        result = _find_passing_transitions(state, {})
        assert len(result) == 1

    def test_guarded_fails_without_evidence(self) -> None:
        state = State(
            id="idle",
            next={
                "go": Transition(
                    trigger="go",
                    target="done",
                    conditions=GuardCondition(conditions={"score": ">=80"}),
                )
            },
        )
        result = _find_passing_transitions(state, {})
        assert len(result) == 0

    def test_guarded_passes_with_evidence(self) -> None:
        state = State(
            id="idle",
            next={
                "go": Transition(
                    trigger="go",
                    target="done",
                    conditions=GuardCondition(conditions={"score": ">=80"}),
                )
            },
        )
        result = _find_passing_transitions(state, {"score": "90"})
        assert len(result) == 1


class TestConditionsMet:
    def test_condition_passes(self) -> None:
        assert _conditions_met({"score": ">=80"}, {"score": "90"})

    def test_condition_fails(self) -> None:
        assert not _conditions_met({"score": ">=80"}, {"score": "70"})


class TestCmdValidate:
    def test_valid_flow(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(flow_file=p, json_output=False)
        assert _cmd_validate(ns) == 0

    def test_valid_flow_json(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(flow_file=p, json_output=True)
        assert _cmd_validate(ns) == 0

    def test_invalid_flow(self, tmp_path: Path) -> None:
        yaml_str = (
            "flow: test\nversion: '1.0'\nexits:\n  - done\n"
            "states:\n  - id: idle\n    next:\n"
            "      go:\n        to: nonexistent\n"
        )
        p = _write_flow(tmp_path, yaml_str)
        ns = _ns(flow_file=p, json_output=False)
        assert _cmd_validate(ns) == 1


class TestCmdStates:
    def test_states_text(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(flow_file=p, json_output=False)
        assert _cmd_states(ns) == 0

    def test_states_json(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(flow_file=p, json_output=True)
        assert _cmd_states(ns) == 0


class TestCmdCheck:
    def test_check_state_text(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            target=None,
            json_output=False,
        )
        assert _cmd_check(ns) == 0

    def test_check_state_json(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            target=None,
            json_output=True,
        )
        assert _cmd_check(ns) == 0

    def test_check_state_with_attrs(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _ATTRS_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            target=None,
            json_output=False,
        )
        assert _cmd_check(ns) == 0

    def test_check_missing_state(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="missing",
            target=None,
            json_output=False,
        )
        assert _cmd_check(ns) == 1

    def test_check_conditions_text(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _GUARDED_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            target="go",
            json_output=False,
        )
        assert _cmd_check(ns) == 0

    def test_check_conditions_json(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _GUARDED_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            target="go",
            json_output=True,
        )
        assert _cmd_check(ns) == 0

    def test_check_missing_target(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            target="missing",
            json_output=False,
        )
        assert _cmd_check(ns) == 1

    def test_check_unguarded_conditions(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            target="go",
            json_output=False,
        )
        assert _cmd_check(ns) == 0


class TestCmdNext:
    def test_next_text(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            json_output=False,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_next(ns) == 0

    def test_next_json(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            json_output=True,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_next(ns) == 0

    def test_next_missing_state(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="missing",
            json_output=False,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_next(ns) == 1


class TestCmdTransition:
    def test_transition_text(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            trigger="go",
            json_output=False,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_transition(ns) == 0

    def test_transition_json(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            trigger="go",
            json_output=True,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_transition(ns) == 0

    def test_transition_missing_state(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="missing",
            trigger="go",
            json_output=False,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_transition(ns) == 1

    def test_transition_missing_trigger(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            trigger="missing",
            json_output=False,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_transition(ns) == 1

    def test_transition_conditions_not_met(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _GUARDED_YAML)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            trigger="go",
            json_output=False,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_transition(ns) == 1

    def test_transition_subflow_entry(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SUBFLOW_YAML, "parent.yaml")
        _write_flow(tmp_path, _CHILD_YAML, "child.yaml")
        ns = _ns(
            flow_file=p,
            state_id="idle",
            trigger="start",
            json_output=False,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_transition(ns) == 0

    def test_transition_into_subflow(self, tmp_path: Path) -> None:
        """Transition resolves subflow entry to flow/first-state."""
        p = _write_flow(tmp_path, _SUBFLOW_YAML, "parent.yaml")
        _write_flow(tmp_path, _CHILD_YAML, "child.yaml")
        ns = _ns(
            flow_file=p,
            state_id="idle",
            trigger="start",
            json_output=True,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_transition(ns) == 0

    def test_transition_state_with_missing_subflow(self, tmp_path: Path) -> None:
        """Transition to state with flow ref but no subflow file."""
        yaml_no_child = (
            "flow: test\nversion: '1.0'\nexits:\n  - exit_done\n"
            "states:\n  - id: idle\n    next:\n"
            "      go:\n        to: review\n"
            "  - id: review\n    flow: missing.yaml\n"
            "    next: {}\n"
        )
        p = _write_flow(tmp_path, yaml_no_child)
        ns = _ns(
            flow_file=p,
            state_id="idle",
            trigger="go",
            json_output=False,
            evidence=[],
            evidence_json=None,
        )
        assert _cmd_transition(ns) == 0


class TestCmdCheckState:
    def test_check_state_with_flow_ref(self, tmp_path: Path) -> None:
        """Check state shows flow reference."""
        p = _write_flow(tmp_path, _SUBFLOW_YAML, "parent.yaml")
        _write_flow(tmp_path, _CHILD_YAML, "child.yaml")
        ns = _ns(
            flow_file=p,
            state_id="review",
            target=None,
            json_output=False,
        )
        assert _cmd_check(ns) == 0


class TestCmdMermaid:
    def test_mermaid_text(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(flow_file=p, json_output=False)
        assert _cmd_mermaid(ns) == 0

    def test_mermaid_json(self, tmp_path: Path) -> None:
        p = _write_flow(tmp_path, _SIMPLE_YAML)
        ns = _ns(flow_file=p, json_output=True)
        assert _cmd_mermaid(ns) == 0


class TestMainErrorPaths:
    def test_unknown_command_exits_2(self, tmp_path: Path) -> None:
        import sys

        p = _write_flow(tmp_path, _SIMPLE_YAML)
        with patch.object(sys, "argv", ["flowr", "bogus", str(p)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_file_not_found_exits_2(self) -> None:
        import sys

        with patch.object(sys, "argv", ["flowr", "validate", "/nonexistent.yaml"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2

    def test_invalid_yaml_exits_1(self, tmp_path: Path) -> None:
        import sys

        p = _write_flow(tmp_path, "just a string\n")
        with patch.object(sys, "argv", ["flowr", "validate", str(p)]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
