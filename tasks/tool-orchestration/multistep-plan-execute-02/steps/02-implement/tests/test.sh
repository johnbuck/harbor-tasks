#!/bin/bash
# Write a fixture where "apple" clearly dominates, run wordfreq.py, check stdout.
mkdir -p /logs/verifier
cat > /tmp/fixture.txt <<'EOF'
apple banana apple cherry apple banana apple grape apple
EOF

if [ ! -f /app/wordfreq.py ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi

output=$(python /app/wordfreq.py /tmp/fixture.txt 2>/dev/null | tr -d '[:space:]')

if [ "$output" = "apple" ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi
