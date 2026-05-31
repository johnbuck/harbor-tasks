#!/bin/bash
mkdir -p /logs/verifier
ok=0
python3 -c "
import sys; sys.path.insert(0, '/app')
from calc import add, multiply
assert add(2, 3) == 5
assert multiply(4, 5) == 20
assert multiply(0, 99) == 0
print('OK')
" >/dev/null 2>&1 && ok=1
cat > /logs/verifier/reward.json <<EOF
{"reward": ${ok}, "correctness": ${ok}}
EOF
