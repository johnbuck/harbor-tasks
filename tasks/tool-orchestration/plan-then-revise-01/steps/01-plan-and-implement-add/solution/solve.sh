#!/bin/bash
cat > /app/PLAN.md <<'EOF'
# PLAN

Project-wide rule (kickoff): every arithmetic result is clamped to the
inclusive range [-1000, 1000] via a shared _clamp helper.

1. add(a, b) -> int       : clamp(a + b)
2. multiply(a, b) -> int  : clamp(a * b)
3. divide(a, b) -> float  : clamp(a / b)
4. compose(*ops) -> callable : chain unary ops
EOF
cat > /app/calc.py <<'EOF'
def _clamp(x: int) -> int:
    """Clamp x to the project-wide range [-1000, 1000]."""
    return max(-1000, min(1000, x))


def add(a: int, b: int) -> int:
    return _clamp(a + b)
EOF
