#!/bin/bash
mkdir -p /logs/verifier
ok=0
python3 -c "
import sys; sys.path.insert(0, '/app')
from calc import add, multiply, divide, compose, dispatch, REGISTRY
assert add(2, 3) == 5
assert multiply(4, 5) == 20
assert multiply(0, 99) == 0
assert multiply(50, 50) == 1000   # clamp policy still applied
assert divide(10, 2) == 5
assert compose('add', 'multiply', 2, 3, 4) == 20
assert dispatch('multiply', 4, 5) == 20
assert set(REGISTRY) >= {'add', 'multiply', 'divide', 'compose'}
print('OK')
" >/dev/null 2>&1 && ok=1
cat > /logs/verifier/reward.json <<EOF
{"reward": ${ok}, "correctness": ${ok}}
EOF
