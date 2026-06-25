#!/bin/bash
# Plan-step gate (informational; only the FINAL step counts toward task reward).
# Requires >=4 numbered items AND that the plan names all four modes plus the
# two-decimal and absolute-zero/exit-2 requirements.
mkdir -p /logs/verifier
if [ ! -f /app/plan.md ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi
p=$(tr '[:upper:]' '[:lower:]' < /app/plan.md)
count=$(grep -cE '^[[:space:]]*[0-9]+[.)]' /app/plan.md || true)
ok=1
[ "$count" -ge 4 ] || ok=0
for kw in c2f f2c c2k k2c; do echo "$p" | grep -q "$kw" || ok=0; done
echo "$p" | grep -qE 'two decimal|2 decimal|\.2f|two-decimal' || ok=0
echo "$p" | grep -qE 'absolute zero|273\.15|exit.*2|status.*2|code 2' || ok=0
if [ "$ok" -eq 1 ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi
