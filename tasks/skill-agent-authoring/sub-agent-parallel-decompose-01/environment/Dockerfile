FROM harbor-agents-rich:latest
WORKDIR /app

# Stage 32 input CSVs and one expected-output spec per file. Each file has the
# same nominal shape (id,name,score). The transformation is a 3-stage pipeline:
#   1. filter rows where score >= 50 (rows whose score is missing/non-integer
#      are INVALID and must be dropped, not crashed on)
#   2. sort by score descending (ties: original input order — stable)
#   3. append a summary footer line: SUMMARY,<count>,<sum_of_scores>
# Each of the 3 stages is independently graded, so partial-but-plausible
# outputs earn fractional credit.
#
# Adversarial wrinkles seeded into the inputs (a naive single-pass mishandles):
#   - boundary rows: score exactly 50 is KEPT; 49 is dropped.
#   - malformed score rows ("", "N/A", "  ", "73x") must be skipped silently.
#   - deliberate score ties whose required order is the ORIGINAL input order
#     (a non-stable sort reorders them and fails the sort stage).
#   - a few files filter down to ZERO kept rows -> footer must be SUMMARY,0,0.
RUN mkdir -p /app/inputs /app/expected
RUN python3 - <<'PY'
import csv, random
random.seed(42)
NAMES = ["alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel","india","<prod-group>","kilo","lima","mike","november","oscar","papa","quebec","romeo","sierra","tango"]

def is_int(s):
    try:
        int(s); return True
    except (ValueError, TypeError):
        return False

# Malformed score tokens to sprinkle in. These are NOT integers; they must be
# dropped at the filter stage without crashing the pipeline.
BAD_TOKENS = ["", "N/A", "  ", "73x", "fifty", "--"]

for i in range(1, 33):
    rows = []
    nid = 1
    for _ in range(40):
        rows.append([nid, random.choice(NAMES), str(random.randint(0, 100))])
        nid += 1
    # Inject boundary rows on most files: exactly 50 (kept) and 49 (dropped).
    if i % 2 == 0:
        rows.append([nid, "edgekeep", "50"]); nid += 1
        rows.append([nid, "edgedrop", "49"]); nid += 1
    # Inject malformed-score rows on every 3rd file.
    if i % 3 == 0:
        rows.append([nid, "badrow", random.choice(BAD_TOKENS)]); nid += 1
        rows.append([nid, "badrow2", random.choice(BAD_TOKENS)]); nid += 1
    # Force a deliberate tie cluster on every 4th file: three rows with the
    # same high score in a known input order; stable sort must preserve it.
    if i % 4 == 0:
        tie = random.randint(60, 99)
        rows.append([nid, "tieA", str(tie)]); nid += 1
        rows.append([nid, "tieB", str(tie)]); nid += 1
        rows.append([nid, "tieC", str(tie)]); nid += 1
    # A couple of files: make EVERYTHING below threshold so output is empty.
    if i in (7, 23):
        rows = [[j + 1, random.choice(NAMES), str(random.randint(0, 49))]
                for j in range(12)]

    with open(f"/app/inputs/data_{i:02d}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "name", "score"]); w.writerows(rows)

    # Expected output: filter (valid-int score >= 50), STABLE sort desc, footer.
    valid = [r for r in rows if is_int(r[2])]
    kept = [r for r in valid if int(r[2]) >= 50]
    kept_sorted = sorted(kept, key=lambda r: -int(r[2]))  # Python sort is stable
    cnt = len(kept_sorted)
    total = sum(int(r[2]) for r in kept_sorted)
    with open(f"/app/expected/data_{i:02d}.filtered.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id", "name", "score"])
        w.writerows(kept_sorted)
        w.writerow(["SUMMARY", cnt, total])
PY

# Heartbeat: log file the agent appends to as it begins/ends each file. The
# verifier infers parallelism (max concurrent overlapping intervals) from
# timestamps. Sub-agent harnesses produce >1 concurrent interval.
RUN mkdir -p /var/log && touch /var/log/work.log && chmod 666 /var/log/work.log
