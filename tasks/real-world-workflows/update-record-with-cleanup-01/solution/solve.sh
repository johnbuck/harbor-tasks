#!/bin/bash
# Reference solution — used by the `oracle` agent. Applies the cleanup rules to
# the input ledger and overwrites it in place:
#   * collapse each May-2026 grocery duplicate group to one row
#   * leave every other month, every non-grocery row, and all near-amount /
#     different-category / different-date rows untouched
#   * split the May-2026 1800 rent row into two 900 rows (alex + Sam)
set -e
python3 - <<'PY'
import csv
SRC = "/app/budget.csv"
rows = []
with open(SRC, newline="") as f:
    r = csv.reader(f)
    header = next(r)
    for row in r:
        if len(row) == 6:
            rows.append(tuple(c for c in row))

RENT_ORIG = ("2026-05-15", "rent", "Landlord", "1800.00", "alex", "may 2026 rent")
out, seen = [], set()
for row in rows:
    date, cat, vendor, amt, paid, notes = row
    if cat == "groceries" and date.startswith("2026-05"):
        key = (date, vendor, amt, cat)
        if key in seen:
            continue            # drop subsequent copies of a May grocery dup
        seen.add(key)
        out.append(row)
    elif row == RENT_ORIG:
        n = "may 2026 rent (split with Sam)"
        out.append((date, cat, vendor, "900.00", "alex", n))
        out.append((date, cat, vendor, "900.00", "Sam", n))
    else:
        out.append(row)        # everything else preserved verbatim

with open(SRC, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(header)
    w.writerows(out)
PY
