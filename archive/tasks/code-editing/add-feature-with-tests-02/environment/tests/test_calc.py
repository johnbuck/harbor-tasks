import pytest

from calc import evaluate


def test_single_number():
    assert evaluate("42") == 42.0


def test_addition():
    assert evaluate("1 + 2") == 3.0


def test_precedence():
    assert evaluate("2 + 3 * 4") == 14.0


def test_parentheses_override_precedence():
    assert evaluate("(2 + 3) * 4") == 20.0


def test_subtraction_left_assoc():
    assert evaluate("10 - 3 - 2") == 5.0


def test_division():
    assert evaluate("12 / 4 / 3") == 1.0


def test_decimals():
    assert evaluate("1.5 * 2") == 3.0


def test_unary_minus():
    assert evaluate("-3 + 4") == 1.0


def test_unary_minus_in_product():
    assert evaluate("2 * -4") == -8.0


def test_nested_parens():
    assert evaluate("((1 + 2) * (3 + 4))") == 21.0


def test_whitespace_insensitive():
    assert evaluate("  2*(3+4) ") == 14.0


def test_no_eval_used():
    src = open("/app/calc.py").read()
    assert "eval(" not in src and "exec(" not in src
