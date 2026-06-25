#!/bin/bash
cat > /app/PLAN.md <<'EOF'
# PLAN

Project-wide rule (kickoff): every arithmetic result is clamped to the
inclusive range [-1000, 1000] via a shared _clamp helper.

Dispatch design: REGISTRY maps op name -> function; dispatch(op, *args) looks
the op up and runs it, raising ValueError on an unknown op.

1. add(a, b)       : clamp(a + b)
2. multiply(a, b)  : clamp(a * b)
3. divide(a, b)    : clamp(a // b); ValueError on b == 0
4. compose(...)    : chain two registered ops via dispatch
EOF
cat > /app/calc.py <<'EOF'
def _clamp(x):
    """Clamp x to the project-wide range [-1000, 1000]."""
    return max(-1000, min(1000, x))


def add(a, b):
    return _clamp(a + b)


def divide(a, b):
    if b == 0:
        raise ValueError("divide by zero")
    return _clamp(a // b)


REGISTRY = {"add": add, "divide": divide}


def dispatch(op, *args):
    if op not in REGISTRY:
        raise ValueError("unknown op: " + str(op))
    return REGISTRY[op](*args)
EOF
