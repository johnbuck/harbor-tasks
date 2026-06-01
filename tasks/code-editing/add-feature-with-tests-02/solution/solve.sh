#!/bin/bash
# Reference solution — recursive-descent evaluator implementing the FULL contract
# (precedence, parens, unary minus, left-assoc, decimals, AND ValueError on
# malformed input; ZeroDivisionError left to propagate). No eval/exec. 1.0.
set -e

cat > /app/calc.py <<'EOF'
"""Infix arithmetic evaluator (recursive descent). No eval/exec."""

import re

_TOKEN = re.compile(r"\d+\.\d+|\d+|[()+\-*/]")


def _tokenize(expr: str):
    tokens = []
    pos = 0
    n = len(expr)
    while pos < n:
        if expr[pos].isspace():
            pos += 1
            continue
        m = _TOKEN.match(expr, pos)
        if not m:
            raise ValueError(f"unexpected character at {pos}: {expr[pos:]!r}")
        tokens.append(m.group(0))
        pos = m.end()
    return tokens


def evaluate(expr: str) -> float:
    tokens = _tokenize(expr)
    if not tokens:
        raise ValueError("empty expression")
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def consume(expected=None):
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError("unexpected end of expression")
        t = tokens[pos]
        if expected is not None and t != expected:
            raise ValueError(f"expected {expected!r}, got {t!r}")
        pos += 1
        return t

    def parse_expr():
        value = parse_term()
        while peek() in ("+", "-"):
            op = consume()
            rhs = parse_term()
            value = value + rhs if op == "+" else value - rhs
        return value

    def parse_term():
        value = parse_factor()
        while peek() in ("*", "/"):
            op = consume()
            rhs = parse_factor()
            value = value * rhs if op == "*" else value / rhs
        return value

    def parse_factor():
        t = peek()
        if t is None:
            raise ValueError("unexpected end of expression")
        if t == "-":
            consume()
            return -parse_factor()
        if t == "(":
            consume()
            value = parse_expr()
            consume(")")
            return value
        if t in (")", "+", "*", "/"):
            raise ValueError(f"unexpected token {t!r}")
        return float(consume())

    value = parse_expr()
    if pos != len(tokens):
        raise ValueError(f"trailing tokens: {tokens[pos:]!r}")
    return float(value)
EOF
