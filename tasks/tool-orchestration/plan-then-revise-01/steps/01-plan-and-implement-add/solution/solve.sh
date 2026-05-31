#!/bin/bash
cat > /app/PLAN.md <<'EOF'
1. add(a, b) -> int  : a + b
2. multiply(a, b) -> int  : a * b
3. divide(a, b) -> float  : a / b
4. compose(*ops) -> callable : chain unary ops
EOF
cat > /app/calc.py <<'EOF'
def add(a: int, b: int) -> int:
    return a + b
EOF
