#!/bin/bash
# Reference solution — used by the `oracle` agent. Applies the cleanup rules to
# the input ledger and overwrites it in place.
set -e
python3 - <<'PY'
import csv
SRC = "/app/budget.csv"
RENT_ORIG = ("2026-05-15","rent","Landlord","1800.00","alex","may rent")
rows=[]
with open(SRC, newline="") as f:
    r=csv.reader(f); header=next(r)
    for row in r:
        if len(row)==6: rows.append(tuple(c for c in row))
out=[]; seen=set()
for row in rows:
    date,cat,vendor,amt,paid,notes=row
    if cat=="groceries" and date.startswith("2026-05"):
        key=(date,vendor,amt,cat)
        if key in seen: continue
        seen.add(key); out.append(row)
    elif row==RENT_ORIG:
        n="may rent (split with roommate)"
        out.append((date,cat,vendor,"900.00","alex",n))
        out.append((date,cat,vendor,"900.00","roommate",n))
    else:
        out.append(row)
with open(SRC,"w",newline="") as f:
    w=csv.writer(f); w.writerow(header)
    for row in out: w.writerow(row)
PY
