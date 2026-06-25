#!/bin/bash
# Implement-step gate (informational; only the FINAL step counts toward reward).
# Spot-checks punctuation stripping + the alphabetical tie-break.
mkdir -p /logs/verifier
if [ ! -f /app/wordfreq.py ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi
# "dog" and "fox" each appear 3x; punctuation must be stripped; tie -> "dog".
printf 'fox, dog. fox! dog? "fox" (dog)\n' > /tmp/fixture.txt
out=$(python /app/wordfreq.py /tmp/fixture.txt 2>/dev/null | tr -d '[:space:]')
if [ "$out" = "dog" ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi
