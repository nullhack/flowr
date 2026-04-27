"""Condition evaluation for flow definition guard conditions."""

import re
from enum import Enum


class ConditionOperator(Enum):
    """Operators for guard condition expressions."""

    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    APPROXIMATELY_EQUAL = "~="


_OPERATOR_PREFIXES: list[tuple[str, ConditionOperator]] = [
    (">=", ConditionOperator.GREATER_THAN_OR_EQUAL),
    ("<=", ConditionOperator.LESS_THAN_OR_EQUAL),
    ("~=", ConditionOperator.APPROXIMATELY_EQUAL),
    ("==", ConditionOperator.EQUALS),
    ("!=", ConditionOperator.NOT_EQUALS),
    (">", ConditionOperator.GREATER_THAN),
    ("<", ConditionOperator.LESS_THAN),
]


def _extract_numeric(s: str) -> float | None:
    """Extract the first numeric value from a string."""
    match = re.search(r"[-+]?\d*\.?\d+", s)
    if match is None:
        return None
    return float(match.group())


def parse_condition(condition_str: str) -> tuple[ConditionOperator, str]:
    """Parse a condition string into an operator and value."""
    for prefix, op in _OPERATOR_PREFIXES:
        if condition_str.startswith(prefix):
            return op, condition_str[len(prefix) :]
    return ConditionOperator.EQUALS, condition_str


def _compare_numeric(
    condition_value: str,
    evidence_value: str,
    op: ConditionOperator,
) -> bool | None:
    """Compare two values numerically. Returns None if not numeric."""
    c_num = _extract_numeric(condition_value)
    e_num = _extract_numeric(evidence_value)
    if c_num is None or e_num is None:
        return None
    match op:
        case ConditionOperator.GREATER_THAN_OR_EQUAL:
            return e_num >= c_num
        case ConditionOperator.LESS_THAN_OR_EQUAL:
            return e_num <= c_num
        case ConditionOperator.GREATER_THAN:
            return e_num > c_num
        case ConditionOperator.LESS_THAN:
            return e_num < c_num
        case ConditionOperator.APPROXIMATELY_EQUAL:
            return abs(e_num - c_num) / abs(c_num) <= 0.05
    return None  # pragma: no cover


def evaluate_condition(
    operator: ConditionOperator,
    condition_value: str,
    evidence_value: str,
) -> bool:
    """Evaluate a condition expression against an evidence value."""
    match operator:
        case ConditionOperator.EQUALS:
            return evidence_value == condition_value
        case ConditionOperator.NOT_EQUALS:
            return evidence_value != condition_value
        case _:
            result = _compare_numeric(condition_value, evidence_value, operator)
            if result is None:
                return False
            return result
