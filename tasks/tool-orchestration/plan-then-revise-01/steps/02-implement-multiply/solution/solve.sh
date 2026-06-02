#!/bin/bash
cat >> /app/calc.py <<'EOF'


def multiply(a: int, b: int) -> int:
    return _clamp(a * b)
EOF
