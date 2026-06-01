#!/bin/bash
# Graded verifier for pandas-sql-from-nl-01.
#
# The agent answers six analysis questions as KEY=value lines. reward = fraction
# answered correctly, so a query that ignores the de-dup / null-handling rules
# (Q1, Q5) or botches the join/groupby (Q3, Q5, Q6) scores a clear fraction
# instead of a saturated 0/1.
#
# Questions graded (6):
#   Q1_WEST_TOTAL            sum with de-dup + null-skip  (naive over-counts dupes)
#   Q2_DISTINCT_REGIONS      distinct non-null regions
#   Q3_TOP_MEAN_REGION       groupby-mean argmax, tie->alpha
#   Q4_MISSING_AMOUNT_ROWS   raw null-amount count (before de-dup)
#   Q5_HARDWARE_GROSS_PROFIT join + filter + sum(amount-unit_cost)  (de-dup matters)
#   Q6_TOP_PRODUCT_BY_AMOUNT groupby-sum argmax, tie->alpha
#
# Numeric answers are compared with a small tolerance; string answers exact
# (case-insensitive, trimmed). reward.json MUST stay a FLAT dict of scalar
# numbers (FOOTGUNS #38).
set -u
mkdir -p /logs/verifier

python3 - <<'PY' > /logs/verifier/reward.json
import json

ANSWER = "/app/answer.txt"

# Ground truth (computed from the baked CSVs).
NUMERIC = {
    "Q1_WEST_TOTAL": 235.25,
    "Q5_HARDWARE_GROSS_PROFIT": 277.00,
}
EXACT = {
    "Q2_DISTINCT_REGIONS": "3",
    "Q3_TOP_MEAN_REGION": "east",          # compared lowercased
    "Q4_MISSING_AMOUNT_ROWS": "2",
    "Q6_TOP_PRODUCT_BY_AMOUNT": "b",       # compared lowercased
}
KEYS = ["Q1_WEST_TOTAL", "Q2_DISTINCT_REGIONS", "Q3_TOP_MEAN_REGION",
        "Q4_MISSING_AMOUNT_ROWS", "Q5_HARDWARE_GROSS_PROFIT",
        "Q6_TOP_PRODUCT_BY_AMOUNT"]
TOL = 0.01

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

checks = {}
for k in KEYS:
    v = parsed.get(k)
    if k in NUMERIC:
        try:
            checks[k] = abs(float(v) - NUMERIC[k]) <= TOL
        except (TypeError, ValueError):
            checks[k] = False
    else:
        checks[k] = (v is not None and v.strip().lower() == EXACT[k])

N = len(KEYS)
satisfied = sum(1 for ok in checks.values() if ok)
reward = round(satisfied / N, 4)
correctness = 1 if satisfied == N else 0

out = {"reward": reward, "correctness": correctness, "satisfied": satisfied, "n_checks": N}
out.update({f"ok_{k.lower()}": int(checks[k]) for k in KEYS})
print(json.dumps(out))
PY

# Tamper check: data files unmodified.
if ! diff -q /app/sales.csv /opt/canonical/sales.csv >/dev/null 2>&1 \
   || ! diff -q /app/products.csv /opt/canonical/products.csv >/dev/null 2>&1; then
    cat > /logs/verifier/reward.json <<EOF
{"reward": 0.0, "correctness": 0, "satisfied": 0, "n_checks": 6, "instruction_following": 0}
EOF
    echo "data file tampered — reward 0" > /logs/verifier/note.log
fi
