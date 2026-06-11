"""Leak-proof, per-decision grader for update-record-with-cleanup-01.

No answer key is ever materialized in the container. This grader reads a pristine
copy of the ORIGINAL ledger (tests/original.csv — the SAME input the agent got,
NOT the answer), classifies every row by the cleanup rules, and scores the
agent's /app/budget.csv per decision. The agent is told only the user goal; it
must DISCOVER the duplicate groups and the preservation traps from the ~340-row,
24-month ledger.

Per-DECISION partial credit (order-independent), so neither "do nothing" nor
"over-dedup everything" scores well:
  * DEDUP   (1 unit / May-2026 grocery duplicate group): collapse to exactly 1.
  * PRESERVE(1 unit / NON-(May groceries) duplicate group): keep ALL copies —
            earlier-month grocery dups + the May utilities triple must survive.
  * RENT    (2 units): the May-2026 1800 rent row replaced by two 900 rows
            (one paid by alex, one by Sam); the original 1800 row gone.
  * COLLATERAL (1 fractional unit): every other original row (near-amount pairs,
            same-date/different-category, same-vendor/different-date singletons,
            and all unrelated months) preserved — guards against over-dedup.

reward = (dedup_ok + preserve_ok + rent_split_ok + rent_orig_gone + collateral_frac) / total.

Format tolerance (kills false-zeros): amounts are normalized to 2 decimals
($/commas stripped) so 900.0 == 900.00; the rent-split halves match on
date/category/vendor/amount/payer only (notes are not mandated); the roommate
name matches case-insensitively. Other fields compare exactly (stripped) — the
agent is not asked to rename vendors/categories. Row ORDER is not graded (the
instruction does not require it). reward.json is a FLAT scalar dict (FOOTGUNS #38).
"""

import csv
import json
from collections import Counter
from pathlib import Path

ORIGINAL = Path("/tests/original.csv")
AGENT = Path("/app/budget.csv")
REWARD = Path("/logs/verifier/reward.json")

RENT_DATE = "2026-05-15"
RENT_VENDOR = "Landlord"
RENT_ORIG_AMT = "1800.00"
RENT_HALF = "900.00"


def canon_amt(a):
    a = a.strip().lstrip("$").replace(",", "")
    try:
        return f"{float(a):.2f}"
    except ValueError:
        return a.strip()


def parse(path):
    rows = []
    if not path.exists():
        return rows
    with path.open(newline="") as f:
        raw = list(csv.reader(f))
    # Header detection: only skip the first line when it actually IS the header
    # (first cell == "date"). A headerless agent file starts with a real data row
    # whose first cell is a date string — skipping it would silently eat that row.
    if raw and raw[0] and raw[0][0].strip().lower() == "date":
        raw = raw[1:]
    for row in raw:
        if len(row) == 6 and any(c.strip() for c in row):
            d, cat, v, amt, paid, notes = (c.strip() for c in row)
            rows.append((d, cat, v, canon_amt(amt), paid, notes))
    return rows


def is_rent_orig(row):
    return (row[0] == RENT_DATE and row[1] == "rent"
            and row[2] == RENT_VENDOR and row[3] == RENT_ORIG_AMT)


def main():
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    orig = parse(ORIGINAL)
    agent = parse(AGENT)
    # Notes are not part of a record's IDENTITY (the rent split already matches on
    # payer not notes). Drop the notes field from the dedup/preserve/collateral
    # key so re-annotating a preserved duplicate does not forfeit preserve credit.
    oc = Counter(row[:5] for row in orig)
    ac = Counter(row[:5] for row in agent)

    dedup_rows, preserve_rows, singletons = [], [], []
    for row, c in oc.items():
        if is_rent_orig(row):
            continue
        is_may_groc = row[1] == "groceries" and row[0].startswith("2026-05")
        if c > 1 and is_may_groc:
            dedup_rows.append(row)
        elif c > 1:
            preserve_rows.append((row, c))
        else:
            singletons.append(row)

    dedup_ok = sum(1 for row in dedup_rows if ac.get(row, 0) == 1)
    preserve_ok = sum(1 for row, c in preserve_rows if ac.get(row, 0) == c)

    def has_rent_half(name):
        for (d, cat, v, amt, paid), n in ac.items():
            if (d == RENT_DATE and cat == "rent" and v == RENT_VENDOR
                    and amt == RENT_HALF and paid.lower() == name):
                return True
        return False

    rent_split_ok = 1 if (has_rent_half("alex") and has_rent_half("sam")) else 0
    rent_orig_gone = 1 if not any(is_rent_orig(r) for r in ac) else 0
    collateral_frac = (sum(1 for row in singletons if ac.get(row, 0) >= 1) / len(singletons)) if singletons else 1.0

    # FLOOR: the preserve + collateral units are trivially earned by doing NOTHING
    # (leaving every original row in place), which let "do nothing" coast to ~0.50.
    # Gate them on having actually deduped: zero real dedup collapses that credit so
    # the floor drops below 0.50, while any genuine dedup unlocks full partial credit.
    dedup_gate = min(1, dedup_ok)
    preserve_ok *= dedup_gate
    collateral_frac *= dedup_gate

    n_dedup, n_preserve = len(dedup_rows), len(preserve_rows)
    total = n_dedup + n_preserve + 2 + 1  # +2 rent units, +1 collateral unit
    earned = dedup_ok + preserve_ok + rent_split_ok + rent_orig_gone + collateral_frac
    reward = round(earned / total, 4)

    out = {
        "reward": reward,
        "answer_present": 1 if agent else 0,
        "dedup_ok": dedup_ok, "dedup_total": n_dedup,
        "preserve_ok": preserve_ok, "preserve_total": n_preserve,
        "rent_split_ok": rent_split_ok, "rent_orig_gone": rent_orig_gone,
        "collateral_frac": round(collateral_frac, 4),
    }
    REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
