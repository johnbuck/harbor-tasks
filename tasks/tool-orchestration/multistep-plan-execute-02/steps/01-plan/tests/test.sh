#!/bin/bash
# Verify /app/plan.md exists and has at least 3 numbered list items.
mkdir -p /logs/verifier
if [ ! -f /app/plan.md ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi
count=$(grep -cE '^[[:space:]]*[0-9]+[.)]' /app/plan.md || true)
if [ "$count" -ge 3 ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi
