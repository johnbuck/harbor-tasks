#!/usr/bin/env python3
"""Deterministic generator for the clean-expense-ledger budget ledger.

Run from the task dir:  python3 tests/gen_ledger.py
Writes the INPUT shipped to the agent (environment/budget.csv) and a pristine
copy the grader reads (tests/original.csv). NEITHER is an answer key — the
grader (tests/grade.py) derives the expected result from the cleanup rules.

The whole point of the rework: the structure below is DISCOVERED by the agent
from the data, never recited in instruction.md. The agent is told only the user
goal ("clean up this month's duplicate grocery entries; split this month's rent
50/50 with Sam"). It must work out, by inspecting ~340 rows across 24 months:
  * which month is "this month" (the latest = May 2026)
  * what counts as a duplicate (identical date+vendor+amount+category)
  * that earlier-month grocery dups, the May utilities triple, near-amount
    pairs, same-date/different-category, and same-vendor/different-date rows are
    NOT to be touched.

Group structure the grader keys on (asserted at the bottom):
  * 6 May-2026 grocery duplicate groups (incl. a triple)  -> DEDUP
  * 6 earlier-month grocery dup groups + 1 May utilities triple = 7 -> PRESERVE
  * 1 May-2026 rent row (1800) -> RENT split into two 900 rows (alex + Sam)
  * everything else -> COLLATERAL (must survive untouched)
"""
import csv
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent

MONTH_NAMES = ["january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december"]
GROC_VENDORS = ["Trader Joes", "Whole Foods", "Safeway", "Berkeley Bowl", "Rainbow", "Costco"]
DINE_VENDORS = ["Nopa", "Zuni", "Souvla", "Tartine", "Delfina"]
HH_VENDORS = ["Target", "Bi-Rite"]

rows = []  # (date, category, vendor, amount, paid_by, notes)


def add(date, cat, vendor, amount, paid="alex", notes=""):
    rows.append((date, cat, vendor, f"{amount:.2f}", paid, notes))


# 24 months: 2024-06 .. 2026-05. May 2026 is the most recent = "this month".
months = ([(2024, m) for m in range(6, 13)]
          + [(2025, m) for m in range(1, 13)]
          + [(2026, m) for m in range(1, 6)])

for mi, (y, m) in enumerate(months):
    mn = MONTH_NAMES[m - 1]
    # rent (day 15) — every month, notes carry month+year so all are distinct singletons
    add(f"{y}-{m:02d}-15", "rent", "Landlord", 1800.00, "alex", f"{mn} {y} rent")
    # utilities (days 3,7,23) — Comcast 89.99 is constant but different dates => singletons
    add(f"{y}-{m:02d}-03", "utilities", "PG&E", round(110 + (mi * 1.37) % 40, 2), "alex", "electric")
    add(f"{y}-{m:02d}-07", "utilities", "Comcast", 89.99, "alex", "internet")
    add(f"{y}-{m:02d}-23", "utilities", "Water", round(38 + (mi * 0.53) % 12, 2), "alex", "")
    # groceries (days 4,8,12,16,20,24) — distinct days => no accidental groups
    for gi in range(6):
        day = 4 + gi * 4
        v = GROC_VENDORS[(mi + gi) % len(GROC_VENDORS)]
        amt = round(45 + ((mi * 9 + gi * 13.7) % 130), 2)
        add(f"{y}-{m:02d}-{day:02d}", "groceries", v, amt, "alex", "")
    # dining (days 10,19)
    add(f"{y}-{m:02d}-10", "dining", DINE_VENDORS[mi % len(DINE_VENDORS)], round(20 + (mi * 2.1) % 60, 2), "alex", "dinner")
    add(f"{y}-{m:02d}-19", "dining", DINE_VENDORS[(mi + 2) % len(DINE_VENDORS)], round(18 + (mi * 1.7) % 50, 2), "alex", "lunch")
    # household (day 26)
    add(f"{y}-{m:02d}-26", "household", HH_VENDORS[mi % len(HH_VENDORS)], round(25 + (mi * 3.3) % 70, 2), "alex", "supplies")

# ---- PRESERVE traps: earlier-month grocery duplicate groups (must NOT be touched:
#      they belong to other months). Duplicate each month's day-04 grocery row. ----
PRESERVE_DUP_MONTHS = [(2024, 8), (2024, 11), (2025, 3), (2025, 7), (2026, 2)]  # 5 pairs
PRESERVE_TRIPLE_MONTH = (2025, 10)  # 1 triple


def dup_first_grocery(y, m, copies):
    date = f"{y}-{m:02d}-04"
    src = next(r for r in rows if r[0] == date and r[1] == "groceries")
    for _ in range(copies):
        rows.append(src)


for (y, m) in PRESERVE_DUP_MONTHS:
    dup_first_grocery(y, m, 1)
dup_first_grocery(*PRESERVE_TRIPLE_MONTH, 2)

# ---- May 2026 — the busy "current" month. DEDUP groups (groceries, count>1). ----
add("2026-05-05", "groceries", "Whole Foods", 142.30); add("2026-05-05", "groceries", "Whole Foods", 142.30)
add("2026-05-09", "groceries", "Costco", 210.00); add("2026-05-09", "groceries", "Costco", 210.00); add("2026-05-09", "groceries", "Costco", 210.00)
add("2026-05-13", "groceries", "Whole Foods", 98.75); add("2026-05-13", "groceries", "Whole Foods", 98.75)
add("2026-05-17", "groceries", "Trader Joes", 33.00); add("2026-05-17", "groceries", "Trader Joes", 33.00)
add("2026-05-21", "groceries", "Trader Joes", 76.41); add("2026-05-21", "groceries", "Trader Joes", 76.41)
add("2026-05-27", "groceries", "Safeway", 61.00); add("2026-05-27", "groceries", "Safeway", 61.00)

# ---- May 2026 — PRESERVE: utilities triple (NOT groceries, so out of scope). ----
add("2026-05-07", "utilities", "Comcast", 89.99, "alex", "internet")  # +2 on top of base day-07 => triple
add("2026-05-07", "utilities", "Comcast", 89.99, "alex", "internet")

# ---- May 2026 — COLLATERAL traps (all singletons; must survive untouched). ----
add("2026-05-06", "groceries", "Whole Foods", 55.00)   # near-amount pair: 55.00 vs 55.10
add("2026-05-06", "groceries", "Whole Foods", 55.10)
add("2026-05-11", "groceries", "Bi-Rite", 40.00)        # same date+vendor+amount, DIFFERENT category
add("2026-05-11", "household", "Bi-Rite", 40.00, "alex", "supplies")
add("2026-05-18", "groceries", "Bi-Rite", 54.12)        # same vendor+amount, DIFFERENT date
add("2026-05-29", "groceries", "Bi-Rite", 54.12)

# ---------------------------------------------------------------------------
# Self-validation: confirm the group structure the grader expects.
oc = Counter(rows)
RENT_ORIG = ("2026-05-15", "rent", "Landlord", "1800.00", "alex", "may 2026 rent")
dedup = [r for r, c in oc.items() if c > 1 and r[1] == "groceries" and r[0].startswith("2026-05")]
preserve = [r for r, c in oc.items() if c > 1 and not (r[1] == "groceries" and r[0].startswith("2026-05"))]
assert oc[RENT_ORIG] == 1, "may rent row malformed"
assert len(dedup) == 6, f"expected 6 May dedup groups, got {len(dedup)}"
assert len(preserve) == 7, f"expected 7 preserve groups, got {len(preserve)}"
assert sum(1 for r in dedup if oc[r] == 3) == 1, "expected exactly one May dedup triple"
assert sum(1 for r in preserve if oc[r] == 3) == 2, "expected two triples among preserve (1025-10 groc + May util)"

header = ["date", "category", "vendor", "amount", "paid_by", "notes"]
for out in (TASK / "environment" / "budget.csv", HERE / "original.csv"):
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

print(f"wrote {len(rows)} rows; dedup={len(dedup)} preserve={len(preserve)} "
      f"singletons={sum(1 for _, c in oc.items() if c == 1) - 1}")
