#!/bin/bash
# Verifier: GRADED on correctness + EFFICIENCY (retry budget), so a harness that
# recovers cleanly in the minimum number of attempts scores higher than one that
# flails through many retries, even though both eventually produce the files.
#
# Attempt counting: flaky-fetch increments /var/log/fetch.counter on EVERY
# invocation (see environment/Dockerfile). The tool deterministically fails on
# calls 1-3 (transient) and succeeds on call 4+, so the minimum number of
# invocations needed to recover is 4. Extra invocations beyond that are wasted
# retries / spamming — the inefficiency signal we want to grade.
#
# Reward = 0.6*correctness + 0.4*efficiency
#   correctness = (payload_ok + token_ok) / 2          (did it reach recovered state)
#   efficiency  = clamp((CEIL - attempts)/(CEIL - IDEAL), 0, 1)
#     IDEAL = 4  (forced floor: 3 transient fails + 1 success = clean recovery)
#     CEIL  = 15 (a harness still looping at this point has no recovery strategy)
# If correctness == 0 (never recovered) efficiency is meaningless and is dropped,
# so a give-up scores ~0 regardless of how few attempts it made.
#
# reward.json MUST stay a FLAT dict of scalar numbers only (Harbor pydantic
# rejects nested dict/list values -> reward=None / trial error; FOOTGUNS #38).

mkdir -p /logs/verifier

payload_ok=0; token_ok=0
if [ -f /app/payload.txt ] && grep -q '^PAYLOAD: hgr-7842-OK$' /app/payload.txt; then
    payload_ok=1
fi
if [ -f /app/token.txt ] && [ "$(cat /app/token.txt 2>/dev/null | tr -d '[:space:]')" = "hgr-7842-OK" ]; then
    token_ok=1
fi

attempts=$(cat /var/log/fetch.counter 2>/dev/null || echo 0)

read reward correctness efficiency <<<"$(python3 -c "
payload_ok = $payload_ok
token_ok   = $token_ok
attempts   = $attempts
IDEAL = 4
CEIL  = 15

correctness = (payload_ok + token_ok) / 2.0
raw = (CEIL - attempts) / float(CEIL - IDEAL)
efficiency = max(0.0, min(1.0, raw))

if correctness == 0:
    reward = 0.6 * correctness  # 0.0 — never recovered; do not credit efficiency
else:
    reward = 0.6 * correctness + 0.4 * efficiency

print(round(reward, 4), round(correctness, 4), round(efficiency, 4))
")"

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "efficiency": ${efficiency}, "attempts": ${attempts}}
EOF
