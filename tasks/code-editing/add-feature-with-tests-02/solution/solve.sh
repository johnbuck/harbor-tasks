#!/bin/bash
set -e

cat > /app/calc.py <<'EOF'
"""Infix arithmetic evaluator (recursive descent)."""

import re

_TOKEN = re.compile(r"\s*(\d+\.\d+|\d+|[()+\-*/])")


def _tokenize(expr: str):
    tokens = []
    pos = 0
    while pos < len(expr):
        if expr[pos].isspace():
            pos += 1
            continue
        m = _TOKEN.match(expr, pos)
        if not m:
            raise ValueError(f"bad token at {pos}: {expr[pos:]!r}")
        tokens.append(m.group(1))
        pos = m.end()
    return tokens


def evaluate(expr: str) -> float:
    tokens = _tokenize(expr)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def consume():
        nonlocal pos
        t = tokens[pos]
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
        if t == "-":
            consume()
            return -parse_factor()
        if t == "(":
            consume()
            value = parse_expr()
            consume()  # ")"
            return value
        return float(consume())

    return float(parse_expr())
EOF
