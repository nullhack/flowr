"""Unit tests for domain/session.py edge cases and config.py coverage."""

from pathlib import Path

import pytest

from flowr.domain.session import Session, SessionStackFrame
from flowr.infrastructure.config import (
    ConfigError,
    resolve_config,
    resolve_config_with_sources,
)


class TestSessionWithState:
    def test_with_state_explicit_timestamp(self) -> None:
        s = Session(flow="f", state="a", name="n")
        updated = s.with_state("b", updated_at="2026-01-01")
        assert updated.state == "b"
        assert updated.updated_at == "2026-01-01"

    def test_with_state_auto_timestamp(self) -> None:
        s = Session(flow="f", state="a", name="n")
        updated = s.with_state("b")
        assert updated.state == "b"
        assert updated.updated_at != ""

    def test_push_stack_default_flow(self) -> None:
        s = Session(flow="f", state="a", name="n")
        frame = SessionStackFrame(flow="parent", state="middle")
        updated = s.push_stack(frame, "sub-start")
        assert updated.flow == "f"
        assert updated.state == "sub-start"
        assert len(updated.stack) == 1

    def test_push_stack_new_flow(self) -> None:
        s = Session(flow="f", state="a", name="n")
        frame = SessionStackFrame(flow="parent", state="middle")
        updated = s.push_stack(frame, "sub-start", new_flow="child")
        assert updated.flow == "child"
        assert updated.state == "sub-start"

    def test_pop_stack_restores_parent_flow(self) -> None:
        s = Session(
            flow="child",
            state="sub-done",
            name="n",
            stack=[SessionStackFrame(flow="parent", state="middle")],
        )
        updated = s.pop_stack("complete")
        assert updated.flow == "parent"
        assert updated.state == "complete"
        assert len(updated.stack) == 0

    def test_pop_stack_empty_uses_current_flow(self) -> None:
        s = Session(flow="f", state="done", name="n", stack=[])
        updated = s.pop_stack("idle")
        assert updated.flow == "f"
        assert updated.state == "idle"


class TestConfigResolveConfig:
    def test_defaults(self, tmp_path: Path) -> None:
        config = resolve_config(project_root=tmp_path)
        assert config.flows_dir == Path(".flowr/flows")
        assert config.default_flow == "main-flow"

    def test_pyproject_values(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text(
            '[tool.flowr]\nflows_dir = "custom/flows"\ndefault_flow = "my-flow"\n'
        )
        config = resolve_config(project_root=tmp_path)
        assert config.flows_dir == Path("custom/flows")
        assert config.default_flow == "my-flow"

    def test_cli_overrides(self, tmp_path: Path) -> None:
        config = resolve_config(
            project_root=tmp_path,
            cli_overrides={"flows_dir": "/override/flows"},
        )
        assert config.flows_dir == Path("/override/flows")

    def test_malformed_pyproject_raises(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("{{invalid toml")
        with pytest.raises(ConfigError):
            resolve_config(project_root=tmp_path)

    def test_missing_pyproject_uses_defaults(self, tmp_path: Path) -> None:
        config = resolve_config(project_root=tmp_path / "nonexistent")
        assert config.default_flow == "main-flow"

    def test_flows_path_and_sessions_path(self, tmp_path: Path) -> None:
        config = resolve_config(project_root=tmp_path)
        assert config.flows_path() == tmp_path / ".flowr" / "flows"
        assert config.sessions_path() == tmp_path / ".flowr" / "sessions"


class TestConfigResolveWithSources:
    def test_default_sources(self, tmp_path: Path) -> None:
        _config, sources = resolve_config_with_sources(project_root=tmp_path)
        assert sources["flows_dir"] == "default"
        assert sources["default_flow"] == "default"
        assert sources["project_root"] == "cwd"

    def test_pyproject_sources(self, tmp_path: Path) -> None:
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.flowr]\ndefault_flow = "custom"\n')
        _config, sources = resolve_config_with_sources(project_root=tmp_path)
        assert sources["default_flow"] == "pyproject.toml"

    def test_cli_override_sources(self, tmp_path: Path) -> None:
        _config, sources = resolve_config_with_sources(
            project_root=tmp_path,
            cli_overrides={"flows_dir": "/custom"},
        )
        assert sources["flows_dir"] == "cli"

    def test_string_path_conversion(self, tmp_path: Path) -> None:
        config = resolve_config(
            project_root=tmp_path,
            cli_overrides={"flows_dir": "/str/path", "sessions_dir": "/str/sess"},
        )
        assert isinstance(config.flows_dir, Path)
        assert isinstance(config.sessions_dir, Path)
