#!/bin/bash
mkdir -p /logs/verifier
ok=0
[ -f /app/PLAN.md ] && [ -s /app/PLAN.md ] && plan_ok=1 || plan_ok=0
if [ -f /app/calc.py ]; then
    python3 -c "
import sys; sys.path.insert(0, '/app')
from calc import add
assert add(2, 3) == 5
assert add(-1, 1) == 0
print('OK')
" >/dev/null 2>&1 && ok=1
fi
reward=$(python3 -c "print(($plan_ok + $ok) / 2.0)")
cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${ok}, "plan_written": ${plan_ok}}
EOF
