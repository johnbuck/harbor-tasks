#!/bin/bash
# Oracle — step 1: scaffold tempconv with three stubs + a test suite.
set -e

mkdir -p /app/tempconv /app/tests

cat > /app/tempconv/__init__.py <<'EOF'
def c_to_f(c):
    raise NotImplementedError

def f_to_c(f):
    raise NotImplementedError

def round_temp(t, ndigits=1):
    raise NotImplementedError
EOF

cat > /app/tests/test_tempconv.py <<'EOF'
import pytest
from tempconv import c_to_f, f_to_c, round_temp

def test_boiling():
    assert c_to_f(100) == 212.0

def test_freezing():
    assert c_to_f(0) == 32.0

def test_f_to_c():
    assert f_to_c(32) == 0.0

def test_round_temp():
    assert round_temp(98.599) == 98.6

def test_below_absolute_zero():
    with pytest.raises(ValueError):
        c_to_f(-300)
EOF
