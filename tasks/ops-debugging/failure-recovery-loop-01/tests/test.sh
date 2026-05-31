#!/bin/bash
# Verifier: both files exist + token matches. Also emits a `retries` axis
# capturing how many flaky-fetch invocations the agent made (3 = optimal,
# higher = inefficient retry pattern, lower = task failed before reaching
# success). Reads /var/log/fetch.counter populated by flaky-fetch itself.

mkdir -p /logs/verifier

payload_ok=0; token_ok=0
if [ -f /app/payload.txt ] && grep -q '^PAYLOAD: hgr-7842-OK$' /app/payload.txt; then
    payload_ok=1
fi
if [ -f /app/token.txt ] && [ "$(cat /app/token.txt 2>/dev/null | tr -d '[:space:]')" = "hgr-7842-OK" ]; then
    token_ok=1
fi

retries=$(cat /var/log/fetch.counter 2>/dev/null || echo 0)
correctness=$(python3 -c "print(($payload_ok + $token_ok) / 2.0)")

# reward = correctness, with a small efficiency penalty if retries > 8 (suggests
# either no retry strategy or panicked spamming). Floor at 0.
reward=$(python3 -c "
import sys
c = $correctness; r = $retries
if c == 0:
    print(0.0)
elif r > 8:
    print(max(0.0, c - 0.1 * (r - 8)))
else:
    print(c)
")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "retries": ${retries}}
EOF
