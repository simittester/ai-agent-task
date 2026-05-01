"""Unit tests for the calculator tool."""

import math

import pytest

from src.tools.calculator import calculator


def test_addition():
    r = calculator("2 + 3")
    assert r["ok"] is True
    assert r["result"] == 5


def test_operator_precedence_and_parentheses():
    assert calculator("2 + 3 * 4")["result"] == 14
    assert calculator("(2 + 3) * 4")["result"] == 20


def test_power_and_unary():
    assert calculator("-2 ** 3")["result"] == -8
    assert calculator("(-2) ** 3")["result"] == -8


def test_division_and_zero_division():
    assert calculator("10 / 4")["result"] == 2.5
    bad = calculator("1 / 0")
    assert bad["ok"] is False
    assert "ZeroDivision" in bad["error"]


def test_allowed_functions():
    assert calculator("sqrt(16)")["result"] == 4.0
    r = calculator("sin(0)")
    assert math.isclose(r["result"], 0.0)


def test_disallowed_function_is_rejected():
    bad = calculator("__import__('os').system('echo hi')")
    assert bad["ok"] is False


def test_empty_input_is_rejected():
    bad = calculator("   ")
    assert bad["ok"] is False
    assert "non-empty" in bad["error"]


def test_invalid_syntax_is_rejected():
    bad = calculator("2 +")
    assert bad["ok"] is False


@pytest.mark.parametrize("expr,expected", [
    ("1 + 1", 2),
    ("100 - 1", 99),
    ("3 * 7", 21),
    ("abs(-5)", 5),
    ("round(3.7)", 4),
])
def test_table(expr, expected):
    assert calculator(expr)["result"] == expected
