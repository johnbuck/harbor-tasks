#!/bin/bash
# ADAPTIVE-RECOVERY scorer. Recovery here REQUIRES diagnosing each error and
# applying a DIFFERENT correction (region -> provisioned region -> token ->
# release); a blind retry of the same command never succeeds, so CORRECTNESS
# itself discriminates an adaptive harness from a flailing one. Efficiency grades
# how cleanly it recovered, on a call budget.
#
# The success payload is a RANDOM nonce dfetch mints at success time (no offline /
# file-read path to it). We grade against the value dfetch ACTUALLY emitted, read
# from its state file /var/log/dfetch.state — never an expected literal (none
# exists). No successful dfetch call => no nonce => correctness 0 AND efficiency 0
# => reward 0 (VOID), flagged by recovered=0 / answer_present.
#
# Reward = 0.6*correctness + 0.4*efficiency
#   correctness = (payload_ok + token_ok)/2   (0 unless a real success emitted a nonce)
#   efficiency  = 0 if not recovered, else clamp((CEIL - calls)/(CEIL - IDEAL), 0, 1)
#     IDEAL = 6  (realistic error-driven discovery: missing-region, bad-region,
#                 401, stale-lock, --release, success)
#     CEIL  = 18 (still flailing at 3x the discovery cost)
# reward.json MUST be a FLAT scalar dict (Harbor rejects nested; FOOTGUNS #38).
# Provenance / the emitted nonce go in the sibling reward-details.json.
set -u
mkdir -p /logs/verifier

ST=/var/log/dfetch.state
# Nonce dfetch actually emitted on its last successful call (empty if it never
# succeeded). This is the ONLY source of the expected value.
NONCE="$(sed -n 's/^NONCE=//p' "$ST" 2>/dev/null | head -1)"
recovered=0
if grep -qx 'STATUS=success' "$ST" 2>/dev/null && [ -n "$NONCE" ]; then
  recovered=1
fi

payload_ok=0; token_ok=0
if [ "$recovered" = "1" ]; then
  [ -f /app/payload.txt ] && grep -qx "PAYLOAD: ${NONCE}" /app/payload.txt && payload_ok=1
  [ -f /app/token.txt ] && [ "$(tr -d '[:space:]' < /app/token.txt 2>/dev/null)" = "${NONCE}" ] && token_ok=1
fi

answer_present=0; [ -f /app/payload.txt ] && answer_present=1
calls=$(cat /var/log/dfetch.counter 2>/dev/null || echo 0)

read reward correctness efficiency <<<"$(python3 -c "
p=$payload_ok; t=$token_ok; calls=$calls; recovered=$recovered
IDEAL=6; CEIL=18
correctness=(p+t)/2.0
eff = 0.0 if recovered==0 else max(0.0, min(1.0, (CEIL-calls)/float(CEIL-IDEAL)))
reward = 0.0 if correctness==0 else 0.6*correctness + 0.4*eff
print(round(reward,4), round(correctness,4), round(eff,4))
")"

cat > /logs/verifier/reward.json <<JSON
{"reward": ${reward}, "correctness": ${correctness}, "efficiency": ${efficiency}, "calls": ${calls}, "recovered": ${recovered}, "answer_present": ${answer_present}}
JSON

cat > /logs/verifier/reward-details.json <<JSON
{
  "emitted_nonce": "${NONCE}",
  "payload_ok": ${payload_ok},
  "token_ok": ${token_ok},
  "note": "recovered=0 => no successful dfetch call => VOID (reward 0). Nonce is random per success; expected value read from dfetch state, never a baked literal."
}
JSON
