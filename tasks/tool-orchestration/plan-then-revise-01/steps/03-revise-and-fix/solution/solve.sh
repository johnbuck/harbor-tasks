#!/bin/bash
# Oracle revision. The on-disk calc.py (from setup.sh) ships add/multiply/divide
# UN-clamped and with no _clamp helper, and still carries divide/compose + the
# 4-op REGISTRY. The revision:
#   - removes divide + compose and the old registry/dispatch (scrapped sunk work)
#   - adds subtract, apply_op (name dispatch), OP_NAMES
#   - RE-APPLIES the kickoff clamp policy to EVERY op. The bound value
#     ([-1000,1000]) is NOT on disk and NOT in this step's instruction; the oracle
#     supplies it from the step-1 decision (the memory the discriminator tests).
#   - rewrites PLAN.md to the revised design.
cat > /app/calc.py <<'EOF'
def _clamp(x):
    """Clamp x to the project-wide range [-1000, 1000]."""
    return max(-1000, min(1000, x))


def add(a, b):
    return _clamp(a + b)


def multiply(a, b):
    return _clamp(a * b)


def subtract(a, b):
    return _clamp(a - b)


OP_NAMES = ["add", "multiply", "subtract"]


def apply_op(op, a, b):
    dispatch = {"add": add, "multiply": multiply, "subtract": subtract}
    if op not in dispatch:
        raise ValueError("unknown op: " + str(op))
    return dispatch[op](a, b)
EOF

cat > /app/PLAN.md <<'EOF'
# PLAN (revised)

Project-wide rule (kickoff, unchanged): every arithmetic result is clamped to
the inclusive range [-1000, 1000] via the shared _clamp helper.

1. add(a, b)        : clamp(a + b)
2. multiply(a, b)   : clamp(a * b)
3. subtract(a, b)   : clamp(a - b)
4. apply_op(op,a,b) : name dispatch over add/multiply/subtract; ValueError on
                      unknown op
   OP_NAMES = ["add", "multiply", "subtract"]

(divide and compose were scrapped in the revision and removed from the module.)
EOF
