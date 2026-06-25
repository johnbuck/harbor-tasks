#!/bin/bash
cat >> /app/calc.py <<'EOF'


def multiply(a, b):
    return _clamp(a * b)


def compose(first, second, a, b, c):
    return dispatch(second, dispatch(first, a, b), c)


REGISTRY["multiply"] = multiply
REGISTRY["compose"] = compose
EOF
