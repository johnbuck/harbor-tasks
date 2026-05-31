FROM harbor-agents-rich:latest
WORKDIR /app

# Stage 20 input CSVs and one expected-output spec per file. Each file has the
# same shape (id,name,score). The transformation is a 3-stage pipeline:
#   1. filter rows where score >= 50
#   2. sort by score descending (ties: original order)
#   3. append a summary footer line: SUMMARY,<count>,<sum_of_scores>
# Each of the 3 stages is independently graded, so partial-but-plausible
# outputs earn fractional credit.
RUN mkdir -p /app/inputs /app/expected
RUN python3 - <<'PY'
import csv, random
random.seed(42)
NAMES = ["alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel","india","juliet","kilo","lima","mike","november","oscar","papa","quebec","romeo","sierra","tango"]
for i in range(1, 21):
    rows = [(j+1, random.choice(NAMES), random.randint(0,100)) for j in range(40)]
    with open(f"/app/inputs/data_{i:02d}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id","name","score"]); w.writerows(rows)
    filt = sorted([r for r in rows if r[2] >= 50], key=lambda r: -r[2])
    cnt = len(filt)
    total = sum(r[2] for r in filt)
    with open(f"/app/expected/data_{i:02d}.filtered.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id","name","score"]); w.writerows(filt)
        w.writerow(["SUMMARY", cnt, total])
PY

# Heartbeat: log file the agent appends to as it begins/ends each file. The
# verifier infers parallelism (max concurrent overlapping intervals) from
# timestamps. Sub-agent harnesses produce >1 concurrent interval.
RUN mkdir -p /var/log && touch /var/log/work.log && chmod 666 /var/log/work.log
