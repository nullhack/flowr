"""Core domain types for flow definitions."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Param:
    """A parameter declaration with optional default value."""

    name: str
    default: Any | None = None


@dataclass(frozen=True, slots=True)
class GuardCondition:
    """A when clause mapping evidence keys to condition expressions."""

    conditions: dict[str, str]


@dataclass(frozen=True, slots=True)
class Transition:
    """A trigger-to-target mapping; tracks referenced condition groups."""

    trigger: str
    target: str
    conditions: GuardCondition | None = None
    referenced_condition_groups: frozenset[str] | None = None


@dataclass(frozen=True, slots=True)
class State:
    """A workflow node with transitions, optional subflow, and named conditions."""

    id: str
    next: dict[str, Transition] = field(default_factory=dict)
    flow: str | None = None
    flow_version: str | None = None
    attrs: dict[str, Any] | None = None
    conditions: dict[str, dict[str, str]] | None = None


@dataclass(frozen=True, slots=True)
class Flow:
    """Top-level flow definition with states, exits, and params."""

    flow: str
    version: str
    exits: list[str]
    states: list[State]
    params: list[Param] = field(default_factory=list)
    attrs: dict[str, Any] | None = None
