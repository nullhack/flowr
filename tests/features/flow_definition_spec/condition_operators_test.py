"""Tests for condition operators story."""

from flowr.domain.condition import (
    ConditionOperator,
    evaluate_condition,
    parse_condition,
)


def test_flow_definition_spec_2ce2f6b6() -> None:
    """
    Given: a when condition all_tests_pass: "==true" and evidence all_tests_pass: "true"
    When: the condition is evaluated
    Then: the condition is satisfied
    """
    assert evaluate_condition(ConditionOperator.EQUALS, "true", "true")


def test_flow_definition_spec_34300527() -> None:
    """
    Given: a when condition verdict: "!=pass" and evidence verdict: "fail"
    When: the condition is evaluated
    Then: the condition is satisfied
    """
    assert evaluate_condition(ConditionOperator.NOT_EQUALS, "pass", "fail")


def test_flow_definition_spec_5fb078c6() -> None:
    """
    Given: a when condition score: ">=80%" and evidence score: "92%"
    When: the condition is evaluated
    Then: numeric extraction compares 92 >= 80 and the condition is satisfied
    """
    assert evaluate_condition(
        ConditionOperator.GREATER_THAN_OR_EQUAL,
        "80%",
        "92%",
    )


def test_flow_definition_spec_c43b1128() -> None:
    """
    Given: a when condition errors: "<3" and evidence errors: "1"
    When: the condition is evaluated
    Then: the condition compares 1 < 3 and is satisfied
    """
    assert evaluate_condition(ConditionOperator.LESS_THAN, "3", "1")


def test_flow_definition_spec_7ea0ad82() -> None:
    """
    Given: a when condition score: ">=80%" and evidence score: "75%"
    When: the condition is evaluated
    Then: numeric extraction strips the percent from both values
      and compares 75 >= 80 as false
    """
    assert not evaluate_condition(
        ConditionOperator.GREATER_THAN_OR_EQUAL,
        "80%",
        "75%",
    )


def test_parse_condition_plain_string() -> None:
    """Plain string condition (no prefix) is treated as equality."""
    operator, value = parse_condition("pass")
    assert operator == ConditionOperator.EQUALS
    assert value == "pass"


def test_parse_condition_with_operator() -> None:
    """Condition with operator prefix is parsed correctly."""
    operator, value = parse_condition(">=80%")
    assert operator == ConditionOperator.GREATER_THAN_OR_EQUAL
    assert value == "80%"
