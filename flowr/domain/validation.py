"""Validation of flow definitions against the specification."""

from dataclasses import dataclass, field
from enum import Enum

from flowr.domain.flow_definition import Flow, State


class ConformanceLevel(Enum):
    """Severity levels for validation violations."""

    MUST = "MUST"
    SHOULD = "SHOULD"


@dataclass(frozen=True, slots=True)
class Violation:
    """A validation finding with severity, message, and location."""

    severity: ConformanceLevel
    message: str
    location: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating a flow definition."""

    violations: list[Violation] = field(default_factory=list)

    @property
    def errors(self) -> list[Violation]:
        """MUST-level violations."""
        return [v for v in self.violations if v.severity == ConformanceLevel.MUST]

    @property
    def warnings(self) -> list[Violation]:
        """SHOULD-level violations."""
        return [v for v in self.violations if v.severity == ConformanceLevel.SHOULD]

    @property
    def is_valid(self) -> bool:
        """True if no MUST-level violations exist."""
        return len(self.errors) == 0


def _check_required_fields(
    flow: Flow,
    violations: list[Violation],
) -> None:
    """Check that required fields are present."""
    if not flow.exits:
        violations.append(
            Violation(
                severity=ConformanceLevel.MUST,
                message="Flow definition must have at least one exit",
                location=f"flow:{flow.flow}",
            )
        )
    if not flow.states:
        violations.append(
            Violation(
                severity=ConformanceLevel.MUST,
                message="Flow definition must have at least one state",
                location=f"flow:{flow.flow}",
            )
        )


def _check_next_targets(
    flow: Flow,
    violations: list[Violation],
) -> None:
    """Check that next targets resolve unambiguously."""
    state_ids = {s.id for s in flow.states}
    exit_names = set(flow.exits)

    for state in flow.states:
        for trigger, transition in state.next.items():
            target = transition.target
            in_states = target in state_ids
            in_exits = target in exit_names

            if in_states and in_exits:
                violations.append(
                    Violation(
                        severity=ConformanceLevel.MUST,
                        message=(
                            f"Next target '{target}' in state"
                            f" '{state.id}' is ambiguous:"
                            " matches both a state and an exit"
                        ),
                        location=(f"flow:{flow.flow}/state:{state.id}/next:{trigger}"),
                    )
                )
            elif not in_states and not in_exits:
                violations.append(
                    Violation(
                        severity=ConformanceLevel.MUST,
                        message=(
                            f"Next target '{target}' in state"
                            f" '{state.id}' does not match"
                            " any state or exit"
                        ),
                        location=(f"flow:{flow.flow}/state:{state.id}/next:{trigger}"),
                    )
                )


def _check_subflow_contracts(
    flow: Flow,
    all_flows: list[Flow],
    violations: list[Violation],
) -> None:
    """Check that parent next keys match child exits."""
    flow_map = {f.flow: f for f in all_flows}
    for state in flow.states:
        if state.flow is None or all_flows is None:  # pragma: no cover
            continue
        child_flow = flow_map.get(state.flow)
        if child_flow is None:  # pragma: no cover
            continue
        next_keys = set(state.next.keys())
        child_exits = set(child_flow.exits)
        for key in next_keys - child_exits:
            violations.append(
                Violation(
                    severity=ConformanceLevel.MUST,
                    message=(
                        f"Next key '{key}' in state"
                        f" '{state.id}' does not match"
                        f" any exit in subflow '{state.flow}'"
                    ),
                    location=f"flow:{flow.flow}/state:{state.id}",
                )
            )


def _check_exit_references(
    flow: Flow,
    violations: list[Violation],
) -> None:
    """Check that exits are referenced by at least one transition."""
    for exit_name in flow.exits:
        referenced = any(
            transition.target == exit_name
            for state in flow.states
            for transition in state.next.values()
        )
        if not referenced:
            violations.append(
                Violation(
                    severity=ConformanceLevel.SHOULD,
                    message=(
                        f"Exit '{exit_name}' is not referenced by any state transition"
                    ),
                    location=f"flow:{flow.flow}/exit:{exit_name}",
                )
            )


def _check_cross_flow_cycles(
    root_flow: Flow,
    all_flows: list[Flow],
    violations: list[Violation],
) -> None:
    """Check for cross-flow cycles via DFS."""
    flow_map = {f.flow: f for f in all_flows}
    visited: set[str] = set()
    path: set[str] = set()

    def dfs(flow_name: str) -> None:
        if flow_name in path:
            violations.append(
                Violation(
                    severity=ConformanceLevel.MUST,
                    message=(f"Cross-flow cycle detected involving flow '{flow_name}'"),
                    location=f"flow:{flow_name}",
                )
            )
            return
        if flow_name in visited:  # pragma: no cover
            return
        visited.add(flow_name)
        path.add(flow_name)
        flow = flow_map.get(flow_name)
        if flow is not None:
            for state in flow.states:
                if state.flow is not None:
                    dfs(state.flow)
        path.discard(flow_name)

    dfs(root_flow.flow)


def _check_condition_references(
    flow: Flow,
    violations: list[Violation],
) -> None:
    """Check that all condition references resolve within their state."""
    for state in flow.states:
        if state.conditions is None:
            continue
        for ref in _collect_refs(state):
            if ref not in state.conditions:
                violations.append(
                    Violation(
                        severity=ConformanceLevel.MUST,
                        message=(
                            f"Unknown condition reference '{ref}' in state '{state.id}'"
                        ),
                        location=f"flow:{flow.flow}/state:{state.id}",
                    )
                )


def _collect_refs(state: State) -> set[str]:
    """Collect all referenced condition group names from a state's transitions."""
    refs: set[str] = set()
    for transition in state.next.values():
        if transition.referenced_condition_groups is not None:
            refs |= transition.referenced_condition_groups
    return refs


def _check_unused_condition_groups(
    flow: Flow,
    violations: list[Violation],
) -> None:
    """Check that all defined condition groups are referenced."""
    for state in flow.states:
        if state.conditions is None:
            continue
        referenced = _collect_refs(state)
        for name in state.conditions:
            if name not in referenced:
                violations.append(
                    Violation(
                        severity=ConformanceLevel.SHOULD,
                        message=(
                            f"Condition group '{name}' is defined"
                            f" but never referenced in state '{state.id}'"
                        ),
                        location=f"flow:{flow.flow}/state:{state.id}",
                    )
                )


def validate(
    flow: Flow,
    all_flows: list[Flow] | None = None,
) -> ValidationResult:
    """Validate a flow definition against all specification rules."""
    violations: list[Violation] = []

    _check_required_fields(flow, violations)
    if not flow.states:
        return ValidationResult(violations=violations)

    _check_next_targets(flow, violations)

    if all_flows is not None:
        _check_subflow_contracts(flow, all_flows, violations)
        _check_cross_flow_cycles(flow, all_flows, violations)

    _check_exit_references(flow, violations)
    _check_condition_references(flow, violations)
    _check_unused_condition_groups(flow, violations)

    return ValidationResult(violations=violations)
