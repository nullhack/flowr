"""Unit tests for validation edge cases."""

from flowr.domain.flow_definition import (
    Flow,
    GuardCondition,
    Param,
    State,
    Transition,
)
from flowr.domain.validation import validate


def test_flow_with_both_ambiguous_and_unresolvable_targets() -> None:
    """A flow with multiple next-target violations collects all of them."""
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="start",
                next={
                    "go": Transition(trigger="go", target="nonexistent"),
                },
            ),
        ],
    )
    result = validate(flow)
    assert not result.is_valid
    assert len(result.errors) >= 1


def test_flow_with_params_defaults() -> None:
    """A flow with params and defaults validates successfully."""
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[State(id="start")],
        params=[
            Param(name="verbose", default=False),
            Param(name="feature_slug"),
        ],
    )
    result = validate(flow)
    assert result.is_valid


def test_flow_with_guarded_transition_validates() -> None:
    """A flow with a guarded transition passes validation."""
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["approved"],
        states=[
            State(
                id="review",
                next={
                    "approve": Transition(
                        trigger="approve",
                        target="approved",
                        conditions=GuardCondition(
                            conditions={"score": ">=80%"},
                        ),
                    ),
                },
            ),
        ],
    )
    result = validate(flow)
    assert result.is_valid


def test_unknown_condition_reference_produces_must_error() -> None:
    """A transition referencing an unknown condition group is a MUST violation."""
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="start",
                conditions={"high-score": {"score": ">=80"}},
                next={
                    "go": Transition(
                        trigger="go",
                        target="done",
                        referenced_condition_groups=frozenset({"missing-ref"}),
                    ),
                },
            ),
        ],
    )
    result = validate(flow)
    assert not result.is_valid
    must_messages = [v.message for v in result.errors]
    assert any("Unknown condition reference 'missing-ref'" in m for m in must_messages)


def test_unused_condition_group_produces_should_warning() -> None:
    """A defined condition group that no transition references is a SHOULD warning."""
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="start",
                conditions={"unused-group": {"score": ">=80"}},
                next={
                    "go": Transition(trigger="go", target="done"),
                },
            ),
        ],
    )
    result = validate(flow)
    assert result.is_valid
    should_messages = [v.message for v in result.warnings]
    assert any("unused-group" in m and "never referenced" in m for m in should_messages)


def test_condition_references_and_unused_groups_both_reported() -> None:
    """Both unknown refs and unused groups are reported in the same validation."""
    flow = Flow(
        flow="test-flow",
        version="1.0.0",
        exits=["done"],
        states=[
            State(
                id="start",
                conditions={"unused-group": {"score": ">=80"}},
                next={
                    "go": Transition(
                        trigger="go",
                        target="done",
                        referenced_condition_groups=frozenset({"unknown-ref"}),
                    ),
                },
            ),
        ],
    )
    result = validate(flow)
    assert not result.is_valid
    assert any("Unknown condition reference" in v.message for v in result.errors)
    assert any("never referenced" in v.message for v in result.warnings)
