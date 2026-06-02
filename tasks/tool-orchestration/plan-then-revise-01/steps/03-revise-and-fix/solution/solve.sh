#!/bin/bash
# Oracle revises: writes the new module per REVISION.md, keeps the kickoff clamp
# policy (subtract clamps like add/multiply — the policy value [-1000,1000] is
# remembered from step 1, NOT restated in REVISION.md), omits divide+compose,
# and updates PLAN.md to reflect the revised spec.
cat > /app/calc.py <<'EOF'
def _clamp(x: int) -> int:
    """Clamp x to the project-wide range [-1000, 1000]."""
    return max(-1000, min(1000, x))


def add(a: int, b: int) -> int:
    return _clamp(a + b)


def multiply(a: int, b: int) -> int:
    return _clamp(a * b)


def subtract(a: int, b: int) -> int:
    return _clamp(a - b)


OP_NAMES = ["add", "multiply", "subtract"]


def apply_op(op: str, a: int, b: int) -> int:
    dispatch = {"add": add, "multiply": multiply, "subtract": subtract}
    if op not in dispatch:
        raise ValueError(f"unknown op: {op}")
    return dispatch[op](a, b)
EOF

cat > /app/PLAN.md <<'EOF'
# PLAN (revised per REVISION.md)

Project-wide rule (kickoff, unchanged): every arithmetic result is clamped to
the inclusive range [-1000, 1000] via the shared _clamp helper.

1. add(a, b) -> int       : clamp(a + b)
2. multiply(a, b) -> int  : clamp(a * b)
3. subtract(a, b) -> int  : clamp(a - b)
4. apply_op(op, a, b)     : dispatch add/multiply/subtract; ValueError on unknown
   OP_NAMES = ["add", "multiply", "subtract"]

(The two originally-planned functions, divide and compose, were scrapped per the
revision.)
EOF
