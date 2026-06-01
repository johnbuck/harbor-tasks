#!/bin/bash
# Graded verifier for shell-pipeline-01.
#
# The agent must emit five independent KEY=value sub-results. reward = fraction
# of them that are exactly correct, so a naive one-liner that gets the headline
# but botches the tie-break, the 5xx range, the query-string stripping, or the
# "-" bytes edge case scores a clear fraction instead of a saturated 0/1.
#
# Sub-results graded (5):
#   TOP_500_IP        most-500 IP WITH tie-break by request volume (naive
#                     `uniq -c | sort -rn | head` picks the wrong tied IP)
#   TOTAL_5XX         count over 500-599 (naive grep of "500" misses 502/503)
#   DISTINCT_5XX_IPS  distinct-IP count over 5xx
#   TOP_4XX_PATH      top 4xx path with ?query stripped
#   TOTAL_2XX_BYTES   2xx byte sum treating "-" as 0
#
# reward.json MUST stay a FLAT dict of scalar numbers (FOOTGUNS #38).
set -u
mkdir -p /logs/verifier

python3 - <<'PY' > /logs/verifier/reward.json
import json, re

ANSWER = "/app/answer.txt"

# Ground truth (computed from the baked access.log).
EXPECTED = {
    "TOP_500_IP": "10.0.0.2",        # 10.0.0.2 & 10.0.0.5 tie at 3x500; .2 has
                                     # more total requests -> wins the tie-break.
                                     # A naive `sort -rn | head` picks 10.0.0.5
                                     # (reverse-lexicographic), which is WRONG.
    "TOTAL_5XX": "10",               # 8x500 + 1x502 + 1x503
    "DISTINCT_5XX_IPS": "5",         # .2 .3 .4 .5 .6
    "TOP_4XX_PATH": "/search",       # /search?q=foo+bar x2 (query stripped)
    "TOTAL_2XX_BYTES": "440",        # "-" counted as 0
}
KEYS = list(EXPECTED.keys())

parsed = {}
try:
    for line in open(ANSWER):
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, _, v = line.partition("=")
        parsed[k.strip()] = v.strip()
except FileNotFoundError:
    parsed = {}

checks = {k: (parsed.get(k) == EXPECTED[k]) for k in KEYS}

N = len(KEYS)
satisfied = sum(1 for ok in checks.values() if ok)
reward = round(satisfied / N, 4)
correctness = 1 if satisfied == N else 0

out = {"reward": reward, "correctness": correctness, "satisfied": satisfied, "n_checks": N}
out.update({f"ok_{k.lower()}": int(checks[k]) for k in KEYS})
print(json.dumps(out))
PY

# Tamper check: if the log was modified, zero everything out.
if ! diff -q /app/access.log /opt/canonical/access.log >/dev/null 2>&1; then
    cat > /logs/verifier/reward.json <<EOF
{"reward": 0.0, "correctness": 0, "satisfied": 0, "n_checks": 5, "instruction_following": 0}
EOF
    echo "access.log tampered — reward 0" > /logs/verifier/note.log
fi
