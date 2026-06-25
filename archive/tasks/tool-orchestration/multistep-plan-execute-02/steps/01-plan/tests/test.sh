#!/bin/bash
# Plan-step gate (informational; only the FINAL step counts toward task reward).
# Requires >=4 numbered items AND that the plan names the hard features.
mkdir -p /logs/verifier
if [ ! -f /app/plan.md ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi
p=$(tr '[:upper:]' '[:lower:]' < /app/plan.md)
count=$(grep -cE '^[[:space:]]*[0-9]+[.)]' /app/plan.md || true)
ok=1
[ "$count" -ge 4 ] || ok=0
echo "$p" | grep -qE 'punctuation|strip' || ok=0
echo "$p" | grep -qE 'tie|alphabet' || ok=0
echo "$p" | grep -q -- '--top' || ok=0
echo "$p" | grep -q -- '--min-len' || ok=0
echo "$p" | grep -q -- '--stopwords' || ok=0
if [ "$ok" -eq 1 ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi
