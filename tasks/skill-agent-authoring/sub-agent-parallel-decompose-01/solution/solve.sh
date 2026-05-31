#!/bin/bash
# Oracle: serial processing (oracle just establishes correctness; the parallelism
# axis comes from real harnesses fanning out via sub-agents).
set -u
for i in $(seq -f '%02g' 1 20); do
    echo "$(date -Iseconds) BEGIN data_${i}" >> /var/log/work.log
    python3 - <<PY
import csv
with open(f"/app/inputs/data_${i}.csv") as f:
    rows = list(csv.reader(f))
header = rows[0]
data = [r for r in rows[1:] if int(r[2]) >= 50]
data.sort(key=lambda r: -int(r[2]))
cnt = len(data)
total = sum(int(r[2]) for r in data)
with open(f"/app/data_${i}.filtered.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(header); w.writerows(data)
    w.writerow(["SUMMARY", cnt, total])
PY
    echo "$(date -Iseconds) END data_${i}" >> /var/log/work.log
done
