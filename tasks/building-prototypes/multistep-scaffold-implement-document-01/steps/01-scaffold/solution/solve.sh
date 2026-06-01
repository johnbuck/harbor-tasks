#!/bin/bash
# Oracle — step 1: scaffold the calc package with four stubs + a test suite.
set -e

mkdir -p /app/calc /app/tests

cat > /app/calc/__init__.py <<'EOF'
def add(a, b):
    raise NotImplementedError

def sub(a, b):
    raise NotImplementedError

def mul(a, b):
    raise NotImplementedError

def divide(a, b):
    raise NotImplementedError
EOF

cat > /app/tests/test_calc.py <<'EOF'
import pytest
from calc import add, sub, mul, divide

def test_add():
    assert add(2, 3) == 5

def test_sub():
    assert sub(5, 2) == 3

def test_mul():
    assert mul(4, 3) == 12

def test_divide():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)
EOF
