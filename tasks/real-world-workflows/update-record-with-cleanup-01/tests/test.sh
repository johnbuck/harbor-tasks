#!/bin/bash
# Graded verifier: reward = fraction of independent sub-checks passed.
# Each duplicate-group decision, each edge-case-preservation, the rent split,
# header order, and history preservation is its own +1. A correct full answer
# scores all N; a partial answer scores the fraction it got right. This is a
# GRADED reward (not all-or-nothing) so harness differences in multi-row
# state-tracking surface as a gradient.
set -u
mkdir -p /logs/verifier

ACT=/app/budget.csv
EXP=/app/.budget.expected.csv

python3 - <<'PY' > /logs/verifier/reward.json
import csv, json, os
from collections import Counter

def load(p):
    if not os.path.exists(p):
        return [], []
    with open(p, newline="") as f:
        r = csv.DictReader(f)
        return list(r), (r.fieldnames or [])

actual_rows, actual_header = load("/app/budget.csv")
expected_rows, expected_header = load("/app/.budget.expected.csv")

def key(r):
    try:
        amt = f"{float(r['amount']):.2f}"
    except (ValueError, TypeError, KeyError):
        amt = str(r.get("amount", ""))
    return (
        r.get("date", ""),
        r.get("category", ""),
        r.get("vendor", ""),
        amt,
        r.get("paid_by", ""),
        (r.get("notes", "") or "").strip(),
    )

act = Counter(key(r) for r in actual_rows)
exp = Counter(key(r) for r in expected_rows)

# --- Independent graded sub-checks ---------------------------------------
checks = {}

def has(k, n=1):
    return act.get(k, 0) >= n

def exactly(k, n):
    return act.get(k, 0) == n

# 1. Header / column order preserved
checks["header_order"] = (actual_header == expected_header)

# 2. May groceries duplicate groups correctly collapsed to exactly one each
checks["dedup_wf_142"]   = exactly(("2026-05-05","groceries","Whole Foods","142.30","alex",""), 1)
checks["dedup_costco_3"] = exactly(("2026-05-09","groceries","Costco","210.00","alex","bulk"), 1)
checks["dedup_wf_98"]    = exactly(("2026-05-12","groceries","Whole Foods","98.75","alex",""), 1)
checks["dedup_tj_76"]    = exactly(("2026-05-21","groceries","Trader Joes","76.41","alex",""), 1)

# 3. Edge-case rows that must be PRESERVED (NOT deduped)
checks["keep_march_dupe"] = exactly(("2026-03-18","groceries","Trader Joes","64.20","alex",""), 2)
checks["keep_april_dupe"] = exactly(("2026-04-22","groceries","Whole Foods","103.10","alex",""), 2)
checks["keep_near_dupe_55_00"] = has(("2026-05-06","groceries","Whole Foods","55.00","alex",""))
checks["keep_near_dupe_55_10"] = has(("2026-05-06","groceries","Whole Foods","55.10","alex",""))
checks["keep_birite_groceries"] = has(("2026-05-11","groceries","Bi-Rite","40.00","alex","snacks"))
checks["keep_birite_household"] = has(("2026-05-11","household","Bi-Rite","40.00","alex","paper goods"))
checks["keep_utilities_dupe"] = exactly(("2026-05-14","utilities","Comcast","89.99","alex","internet"), 2)

# 4. May rent split
def rent_rows(amt, payer):
    return act.get(("2026-05-15","rent","Landlord",amt,payer,"may rent (split with roommate)"), 0)
checks["rent_split_alex"]     = rent_rows("900.00","alex") == 1
checks["rent_split_roommate"] = rent_rows("900.00","roommate") == 1
checks["rent_no_1800"] = not any(
    r.get("date")=="2026-05-15" and r.get("category")=="rent"
    and abs(float(r.get("amount","0") or 0) - 1800.00) < 0.01
    for r in actual_rows
)

# 5. History preservation: March/April rent untouched
checks["keep_march_rent"] = has(("2026-03-15","rent","Landlord","1800.00","alex","march rent"))
checks["keep_april_rent"] = has(("2026-04-15","rent","Landlord","1800.00","alex","april rent"))

# 6. No spurious/unexpected rows introduced
unexpected = sum(max(0, c - exp.get(k, 0)) for k, c in act.items())
checks["no_unexpected_rows"] = (unexpected == 0)

# 7. Total amount preserved (sum invariant across the cleanup)
def tot(rows):
    return sum(float(r.get("amount","0") or 0) for r in rows)
total_drift = abs(tot(actual_rows) - tot(expected_rows))
checks["total_amount_ok"] = (total_drift <= 0.01)

# --- aggregate -----------------------------------------------------------
N = len(checks)
satisfied = sum(1 for v in checks.values() if v)
reward = round(satisfied / N, 4)
correctness = 1 if satisfied == N else 0

historic_loss = 0 if (checks["keep_march_rent"] and checks["keep_april_rent"]) else 1

out = {
    "reward": reward,
    "correctness": correctness,
    "satisfied": satisfied,
    "n_checks": N,
    "historic_loss": historic_loss,
    "unexpected_rows": unexpected,
    "total_amount_drift": round(total_drift, 2),
    "actual_total_rows": len(actual_rows),
    "expected_total_rows": len(expected_rows),
}
print(json.dumps(out))
PY
