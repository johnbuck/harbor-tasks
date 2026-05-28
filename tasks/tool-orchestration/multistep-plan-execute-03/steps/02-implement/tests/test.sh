#!/bin/bash
# Run c2f.py with two canonical inputs and check both outputs.
mkdir -p /logs/verifier

if [ ! -f /app/c2f.py ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi

out1=$(python /app/c2f.py 100 2>/dev/null | tr -d '[:space:]')
out2=$(python /app/c2f.py 0 2>/dev/null | tr -d '[:space:]')

if [ "$out1" = "212.0" ] && [ "$out2" = "32.0" ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi
