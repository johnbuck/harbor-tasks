#!/bin/bash
set -e

mkdir -p /app/tempconv /app/tests

cat > /app/tempconv/__init__.py <<'EOF'
def c_to_f(c):
    raise NotImplementedError
EOF

cat > /app/tests/test_tempconv.py <<'EOF'
from tempconv import c_to_f

def test_boiling():
    assert c_to_f(100) == 212.0

def test_freezing():
    assert c_to_f(0) == 32.0
EOF
