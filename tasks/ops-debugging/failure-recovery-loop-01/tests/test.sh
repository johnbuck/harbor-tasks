#!/bin/bash
# ADAPTIVE-RECOVERY scorer. Recovery here REQUIRES diagnosing each error and
# applying a DIFFERENT correction (region -> valid region -> token -> release);
# a blind retry of the same command never succeeds, so CORRECTNESS itself
# discriminates an adaptive harness from a flailing one. Efficiency grades how
# cleanly it recovered, on a call budget.
#
# Reward = 0.6*correctness + 0.4*efficiency
#   correctness = (payload_ok + token_ok)/2
#   efficiency  = clamp((CEIL - calls)/(CEIL - IDEAL), 0, 1)
#     IDEAL = 6  (realistic minimum to DISCOVER all 4 corrections via errors:
#                 missing-region, bad-region, 401, stale-lock, --release, success)
#     CEIL  = 18 (still flailing at 3x the discovery cost)
#   correctness==0 (never recovered) drops efficiency -> reward 0.
# reward.json MUST be a FLAT scalar dict (Harbor rejects nested; FOOTGUNS #38).
mkdir -p /logs/verifier

payload_ok=0; token_ok=0
[ -f /app/payload.txt ] && grep -q '^PAYLOAD: hgr-7842-OK$' /app/payload.txt && payload_ok=1
[ -f /app/token.txt ] && [ "$(tr -d '[:space:]' < /app/token.txt 2>/dev/null)" = "hgr-7842-OK" ] && token_ok=1
calls=$(cat /var/log/dfetch.counter 2>/dev/null || echo 0)

read reward correctness efficiency <<<"$(python3 -c "
p=$payload_ok; t=$token_ok; calls=$calls
IDEAL=6; CEIL=18
correctness=(p+t)/2.0
eff=max(0.0,min(1.0,(CEIL-calls)/float(CEIL-IDEAL)))
reward = 0.0 if correctness==0 else 0.6*correctness + 0.4*eff
print(round(reward,4), round(correctness,4), round(eff,4))
")"

cat > /logs/verifier/reward.json <<JSON
{"reward": ${reward}, "correctness": ${correctness}, "efficiency": ${efficiency}, "calls": ${calls}}
JSON
