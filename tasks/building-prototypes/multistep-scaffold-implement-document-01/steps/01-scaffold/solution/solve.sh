#!/bin/bash
set -e

mkdir -p /app/calc /app/tests

cat > /app/calc/__init__.py <<'EOF'
def add(a, b):
    raise NotImplementedError
EOF

cat > /app/tests/test_calc.py <<'EOF'
from calc import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_zero():
    assert add(-1, 1) == 0
EOF
