#!/bin/bash
mkdir -p /logs/verifier
[ -f /app/PLAN.md ] && [ -s /app/PLAN.md ] && plan_ok=1 || plan_ok=0
ok=0
if [ -f /app/calc.py ]; then
    python3 -c "
import sys; sys.path.insert(0, '/app')
from calc import add, divide, dispatch
assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(900, 900) == 1000     # clamp policy (upper)
assert add(-900, -900) == -1000  # clamp policy (lower)
assert divide(10, 2) == 5
assert divide(5000, 2) == 1000   # divide clamps too
try:
    divide(1, 0); raise SystemExit(1)
except ValueError:
    pass
assert dispatch('add', 2, 3) == 5
try:
    dispatch('nope', 1, 1); raise SystemExit(1)
except ValueError:
    pass
print('OK')
" >/dev/null 2>&1 && ok=1
fi
reward=$(python3 -c "print(($plan_ok + $ok) / 2.0)")
cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${ok}, "plan_written": ${plan_ok}}
EOF
