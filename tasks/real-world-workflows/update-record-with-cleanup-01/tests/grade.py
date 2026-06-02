"""Leak-proof, per-decision grader for update-record-with-cleanup-01.

REWORK (2026-06-01). The deprecated version shipped the answer key to the agent
at world-readable /app/.budget.expected.csv — trivially gameable. This grader
NEVER materializes the answer in the container: it reads a pristine copy of the
ORIGINAL ledger (tests/original.csv — the same INPUT the agent got, not the
answer), applies the cleanup RULES in code to derive the expected result, and
scores the agent's /app/budget.csv against it.

Scoring is per-DECISION (partial credit), so neither "do nothing" nor
"over-dedup everything" scores well — you must make each call correctly:
  * DEDUP   (one unit per May-groceries duplicate group): collapse to exactly 1.
  * PRESERVE(one unit per NON-(May&groceries) duplicate group): keep ALL copies
            (cross-month grocery dups + the May utilities triple must survive).
  * RENT    (2 units): the 1800 may-rent row replaced by two 900 rows
            (alex + roommate, notes appended); the original 1800 row gone.
  * COLLATERAL (fractional unit): every other original row (near-amount pairs,
            same-date-different-category, same-vendor-different-date singles)
            preserved — guards against an over-aggressive dedup dropping them.

reward = (dedup_ok + preserve_ok + rent_ok + collateral_frac) / total_units.
reward.json MUST be a FLAT scalar dict (FOOTGUNS #38).
"""

import csv
import json
from collections import Counter
from pathlib import Path

ORIGINAL = Path("/tests/original.csv")
AGENT = Path("/app/budget.csv")
REWARD = Path("/logs/verifier/reward.json")

RENT_ORIG = ("2026-05-15", "rent", "Landlord", "1800.00", "alex", "may rent")
RENT_NEW_ALEX = ("2026-05-15", "rent", "Landlord", "900.00", "alex", "may rent (split with roommate)")
RENT_NEW_ROOM = ("2026-05-15", "rent", "Landlord", "900.00", "roommate", "may rent (split with roommate)")


def parse(path):
    rows = []
    if not path.exists():
        return rows
    with path.open(newline="") as f:
        r = csv.reader(f)
        header = next(r, None)
        for row in r:
            if len(row) == 6 and any(c.strip() for c in row):
                rows.append(tuple(c.strip() for c in row))
    return rows


def expected_sequence(orig):
    """Apply the cleanup rules in order (used only for the correctness flag)."""
    out, seen = [], set()
    for row in orig:
        date, cat, vendor, amt, paid, notes = row
        if cat == "groceries" and date.startswith("2026-05"):
            key = (date, vendor, amt, cat)
            if key in seen:
                continue
            seen.add(key)
            out.append(row)
        elif row == RENT_ORIG:
            out.append(RENT_NEW_ALEX)
            out.append(RENT_NEW_ROOM)
        else:
            out.append(row)
    return out


def main():
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    orig = parse(ORIGINAL)
    agent = parse(AGENT)
    ac = Counter(agent)
    oc = Counter(orig)

    dedup_rows, preserve_rows, singletons = [], [], []
    for row, c in oc.items():
        date, cat, vendor, amt, paid, notes = row
        is_may_groc = cat == "groceries" and date.startswith("2026-05")
        if c > 1 and is_may_groc:
            dedup_rows.append(row)
        elif c > 1:
            preserve_rows.append((row, c))
        elif row != RENT_ORIG:
            singletons.append(row)

    dedup_ok = sum(1 for row in dedup_rows if ac.get(row, 0) == 1)
    preserve_ok = sum(1 for row, c in preserve_rows if ac.get(row, 0) == c)
    rent_split_ok = 1 if (ac.get(RENT_NEW_ALEX, 0) >= 1 and ac.get(RENT_NEW_ROOM, 0) >= 1) else 0
    rent_orig_gone = 1 if ac.get(RENT_ORIG, 0) == 0 else 0
    collateral_frac = (sum(1 for row in singletons if ac.get(row, 0) >= 1) / len(singletons)) if singletons else 1.0

    n_dedup, n_preserve = len(dedup_rows), len(preserve_rows)
    total = n_dedup + n_preserve + 2 + 1  # +2 rent units, +1 collateral unit
    earned = dedup_ok + preserve_ok + rent_split_ok + rent_orig_gone + collateral_frac
    reward = round(earned / total, 4)

    correctness = 1 if agent == expected_sequence(orig) else 0

    out = {
        "reward": reward,
        "correctness": correctness,
        "dedup_ok": dedup_ok, "dedup_total": n_dedup,
        "preserve_ok": preserve_ok, "preserve_total": n_preserve,
        "rent_split_ok": rent_split_ok, "rent_orig_gone": rent_orig_gone,
        "collateral_frac": round(collateral_frac, 4),
    }
    REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
