#!/bin/bash
# Write-persistence verifier (#92). Reads /app/answer.md — the SAME path the
# agent was told to write — and reports whether the harness actually persisted
# it. answer_present distinguishes the three outcomes:
#   reward 1, answer_present 1  -> wrote the token to the real /app  (FIXED)
#   reward 0, answer_present 1  -> wrote something, but wrong content (miss)
#   reward 0, answer_present 0  -> nothing landed at /app/answer.md   (VOID / still shadowed)
set -e
mkdir -p /logs/verifier
cp /app/answer.md /logs/verifier/answer.md 2>/dev/null || true

python3 - <<'PY' > /logs/verifier/reward.json
import json, re
try:
    raw = open("/app/answer.md").read()
except FileNotFoundError:
    raw = ""
present = 1 if raw.strip() else 0
ok = 1 if re.search(r"PERSISTED-OK", raw) else 0
print(json.dumps({
    "reward": ok,
    "correctness": ok,
    "answer_present": present,
    "answer_chars": len(raw),
}))
PY
