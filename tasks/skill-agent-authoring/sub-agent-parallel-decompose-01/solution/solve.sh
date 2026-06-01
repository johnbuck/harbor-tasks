#!/bin/bash
# Oracle: serial processing (oracle just establishes correctness; the parallelism
# axis comes from real harnesses fanning out via sub-agents).
#
# Robust transform: skip rows whose score is not a valid integer (malformed
# rows must NOT crash the pipeline), keep score >= 50 (boundary 50 kept),
# STABLE sort desc (ties preserve original input order), emit SUMMARY footer
# (empty result -> SUMMARY,0,0).
set -u
for i in $(seq -f '%02g' 1 32); do
    echo "$(date -Iseconds) BEGIN data_${i}" >> /var/log/work.log
    python3 - <<PY
import csv
with open(f"/app/inputs/data_${i}.csv") as f:
    rows = list(csv.reader(f))
header = rows[0]

def as_int(s):
    try:
        return int(s)
    except (ValueError, TypeError):
        return None

valid = [(r, as_int(r[2])) for r in rows[1:]]
kept = [r for r, v in valid if v is not None and v >= 50]
kept.sort(key=lambda r: -int(r[2]))  # Python sort is stable -> ties keep order
cnt = len(kept)
total = sum(int(r[2]) for r in kept)
with open(f"/app/data_${i}.filtered.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(header); w.writerows(kept)
    w.writerow(["SUMMARY", cnt, total])
PY
    echo "$(date -Iseconds) END data_${i}" >> /var/log/work.log
done
