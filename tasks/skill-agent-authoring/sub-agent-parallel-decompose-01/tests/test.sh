#!/bin/bash
# Graded verifier for sub-agent-parallel-decompose-01.
#
# 32 files x 3 independent stages each = 96 sub-checks:
#   stage 1 (filter):  the set of kept data rows == expected set (order-free)
#   stage 2 (sort):    the kept data rows are in the exact expected order
#   stage 3 (summary): the SUMMARY,<count>,<sum> footer is present and correct
#
# base_reward = passed_subchecks / 96  (graded fraction; NOT binary)
# parallelism bonus: scaled by observed max-concurrency from /var/log/work.log.
#   Serial run (max_concurrent<=1) gets no bonus; genuine fan-out earns up to
#   +0.15, but only multiplied by how much of the work is actually correct
#   (a parallel run that produces garbage earns no bonus). Final reward is
#   clamped to 1.0 and still a graded fraction.
set -u
mkdir -p /logs/verifier

# Parallelism inference from work.log
max_concurrent=$(python3 - <<'PY'
import re
events = []
try:
    with open("/var/log/work.log") as f:
        for line in f:
            m = re.match(r"^(\S+)\s+(BEGIN|END)\s+(\S+)", line.strip())
            if m:
                events.append((m.group(1), m.group(2), m.group(3)))
except FileNotFoundError:
    pass
events.sort(key=lambda e: (e[0], 0 if e[1] == "BEGIN" else 1))
open_set, max_open = set(), 0
for ts, kind, file in events:
    if kind == "BEGIN":
        open_set.add(file)
    else:
        open_set.discard(file)
    max_open = max(max_open, len(open_set))
print(max_open)
PY
)

python3 - "$max_concurrent" <<'PY' > /logs/verifier/reward.json
import csv, json, os, sys

max_concurrent = int(sys.argv[1]) if sys.argv[1].isdigit() else 0

def read_csv(path):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, newline="") as f:
            return [r for r in csv.reader(f) if r]
    except Exception:
        return None

passed = 0
total = 0
per_file = {}

for i in range(1, 33):
    name = f"data_{i:02d}"
    exp = read_csv(f"/app/expected/{name}.filtered.csv")
    act = read_csv(f"/app/{name}.filtered.csv")
    checks = {"filter": 0, "sort": 0, "summary": 0}
    if exp is not None and act is not None:
        # Split expected into data rows + summary footer.
        exp_body = [r for r in exp[1:] if r and r[0] != "SUMMARY"]
        exp_summary = next((r for r in exp if r and r[0] == "SUMMARY"), None)
        act_body = [r for r in act[1:] if r and r[0] != "SUMMARY"]
        act_summary = next((r for r in act if r and r[0] == "SUMMARY"), None)
        # stage 1: filter set (order-free) over (id,name,score) tuples
        if {tuple(r) for r in exp_body} == {tuple(r) for r in act_body}:
            checks["filter"] = 1
        # stage 2: exact order
        if exp_body == act_body:
            checks["sort"] = 1
        # stage 3: summary footer correct
        if act_summary is not None and exp_summary is not None and \
           act_summary[:3] == exp_summary[:3]:
            checks["summary"] = 1
    per_file[name] = checks
    passed += sum(checks.values())
    total += 3

base = passed / total if total else 0.0

# Throughput bonus: proportional to fan-out, gated on correctness so a parallel
# garbage run earns nothing. Caps at +0.15.
par_factor = 0.0
if max_concurrent >= 2:
    par_factor = min(1.0, (max_concurrent - 1) / 3.0)  # 2->0.33, 4->1.0
bonus = round(0.15 * par_factor * base, 4)

reward = round(min(1.0, base + bonus), 4)
correctness = 1 if passed == total else 0

print(json.dumps({
    "reward": reward,
    "correctness": correctness,
    "subchecks_passed": passed,
    "subchecks_total": total,
    "base_reward": round(base, 4),
    "max_concurrent": max_concurrent,
    "parallel_bonus": bonus,
}, indent=2))
PY
