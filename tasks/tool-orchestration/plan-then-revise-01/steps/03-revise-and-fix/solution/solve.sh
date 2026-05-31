#!/bin/bash
# Oracle revises: writes the new module per REVISION.md, omits divide+compose,
# and updates PLAN.md to reflect the revised spec.
cat > /app/calc.py <<'EOF'
def add(a: int, b: int) -> int:
    return a + b


def multiply(a: int, b: int) -> int:
    return a * b


def subtract(a: int, b: int) -> int:
    return a - b


OP_NAMES = ["add", "multiply", "subtract"]


def apply_op(op: str, a: int, b: int) -> int:
    dispatch = {"add": add, "multiply": multiply, "subtract": subtract}
    if op not in dispatch:
        raise ValueError(f"unknown op: {op}")
    return dispatch[op](a, b)
EOF

cat > /app/PLAN.md <<'EOF'
# PLAN (revised per REVISION.md)

1. add(a, b) -> int       : a + b
2. multiply(a, b) -> int  : a * b
3. subtract(a, b) -> int  : a - b
4. apply_op(op, a, b)     : dispatch add/multiply/subtract; ValueError on unknown
   OP_NAMES = ["add", "multiply", "subtract"]

(The two originally-planned functions were scrapped per the revision.)
EOF
