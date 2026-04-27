"""Unit tests for condition evaluation edge cases."""

import pytest

from flowr.domain.condition import (
    ConditionOperator,
    _extract_numeric,
    evaluate_condition,
    parse_condition,
)


def test_extract_numeric_with_percent() -> None:
    """Numeric extraction strips non-numeric suffixes."""
    assert _extract_numeric("80%") == pytest.approx(80.0)


def test_extract_numeric_plain_number() -> None:
    """Numeric extraction works on plain numbers."""
    assert _extract_numeric("42") == pytest.approx(42.0)


def test_extract_numeric_no_number() -> None:
    """Numeric extraction returns None for strings without numbers."""
    assert _extract_numeric("pass") is None


def test_evaluate_equals_mismatch() -> None:
    """Equality fails when values differ."""
    assert not evaluate_condition(ConditionOperator.EQUALS, "true", "false")


def test_evaluate_not_equals_same() -> None:
    """Not-equals fails when values are the same."""
    assert not evaluate_condition(ConditionOperator.NOT_EQUALS, "pass", "pass")


def test_evaluate_numeric_with_non_numeric_evidence() -> None:
    """Numeric comparison returns False when evidence has no number."""
    assert not evaluate_condition(
        ConditionOperator.GREATER_THAN_OR_EQUAL,
        "80",
        "pass",
    )


def test_evaluate_numeric_with_non_numeric_condition() -> None:
    """Numeric comparison returns False when condition has no number."""
    assert not evaluate_condition(
        ConditionOperator.GREATER_THAN_OR_EQUAL,
        "pass",
        "80",
    )


def test_parse_condition_all_operators() -> None:
    """All operators are parsed correctly."""
    assert parse_condition("==true")[0] == ConditionOperator.EQUALS
    assert parse_condition("!=pass")[0] == ConditionOperator.NOT_EQUALS
    assert parse_condition(">=80")[0] == ConditionOperator.GREATER_THAN_OR_EQUAL
    assert parse_condition("<=80")[0] == ConditionOperator.LESS_THAN_OR_EQUAL
    assert parse_condition(">80")[0] == ConditionOperator.GREATER_THAN
    assert parse_condition("<3")[0] == ConditionOperator.LESS_THAN
    assert parse_condition("~=100")[0] == ConditionOperator.APPROXIMATELY_EQUAL


def test_approximate_equal_exact_match() -> None:
    """Approximate match passes when values are exactly equal."""
    assert evaluate_condition(
        ConditionOperator.APPROXIMATELY_EQUAL,
        "100",
        "100",
    )


def test_less_than_or_equal() -> None:
    """Less-than-or-equal works for equal values."""
    assert evaluate_condition(
        ConditionOperator.LESS_THAN_OR_EQUAL,
        "80",
        "80",
    )


def test_greater_than() -> None:
    """Greater-than works for strictly greater values."""
    assert evaluate_condition(
        ConditionOperator.GREATER_THAN,
        "50",
        "60",
    )
