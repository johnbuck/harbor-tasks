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
#     IDEAL = 4  (a clean error-driven recovery: bad-region, 401, stale-lock,
#                 --release+success — the minimum that walks the progression)
#     CEIL  = 18 (still flailing at >4x the discovery cost)
#
# FORGERY GATE (calls >= MIN_CALLS). The state file is agent-writable and its
# format is published in the world-readable dfetch tool, so a STATUS=success +
# self-consistent nonce can be FORGED with zero real recovery. A genuine adaptive
# recovery must walk the error progression, which costs at least MIN_CALLS dfetch
# calls; a success state with fewer calls cannot have done the work, so it earns
# no credit (correctness 0 => reward 0, efficiency 0). REBUILD-DEFERRED hardening
# (compiled dfetch with an embedded build-time secret; nonce = HMAC(secret,
# region|token|counter); grader RECOMPUTES the expected nonce instead of trusting
# the state file; tool writes an ordered error-progression log) closes the
# remaining forge-with-N-junk-calls gap and cannot be exercised offline.
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

read reward correctness efficiency recovered calls <<<"$(calls_raw="$calls" python3 -c "
import os, re
p=$payload_ok; t=$token_ok; recovered=$recovered
# Integer hygiene + S4 crash guard + CODE-INJECTION guard: the counter is
# agent-writable (root, world-writable file) and its bytes are NEVER interpolated
# into this interpreter source -- doing so would let crafted content (e.g. a
# triple-quote breakout) inject arbitrary Python and forge the reward. Read it
# from the environment and accept ONLY a strict integer; a poisoned/non-integer
# counter is treated as 'no valid recovery' and as 0 calls in the FLAT output.
s=os.environ['calls_raw'].strip()
if re.fullmatch(r'-?[0-9]+', s):
    calls=int(s); calls_out=calls
else:
    calls=-1; calls_out=0; recovered=0
MIN_CALLS=4; IDEAL=4; CEIL=18
# Forgery gate: a success with fewer than MIN_CALLS dfetch calls cannot have
# walked the error progression -> no credit.
if calls < MIN_CALLS:
    recovered=0
correctness=(p+t)/2.0 if recovered==1 else 0.0
eff = 0.0 if recovered==0 else max(0.0, min(1.0, (CEIL-calls)/float(CEIL-IDEAL)))
reward = 0.0 if correctness==0 else 0.6*correctness + 0.4*eff
print(round(reward,4), round(correctness,4), round(eff,4), recovered, calls_out)
" 2>/dev/null)"

# Belt-and-suspenders fallback: if the scorer produced nothing (e.g. python
# itself failed to start), still emit a FLAT numeric reward so the trial is not
# silently dropped.
if [ -z "${reward:-}" ]; then
  reward=0.0; correctness=0.0; efficiency=0.0; recovered=0; calls=0
fi

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
