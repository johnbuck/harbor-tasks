#!/bin/bash
# Graded verifier for skill-discovery-and-use-01.
#
# 8 files x 2 independent sub-checks = 16 sub-checks:
#   (A) correctness: /app/out/table_XX.json matches the expected structural
#       summary (key-order tolerant deep equality).
#   (B) discovery:   the CORRECT skill (csv-structure-summary) was actually run
#       against this file — proven by its breadcrumb in
#       /app/.skill-runs/csv-structure-summary.log. A harness that grabbed a
#       decoy skill, or re-implemented from scratch, can still get (A) right but
#       fails (B); a harness that found the right skill but ran it on only some
#       files earns partial (B).
#
# reward = passed_subchecks / 16   (graded fraction; NOT binary)
set -u
mkdir -p /logs/verifier

python3 - <<'PY' > /logs/verifier/reward.json
import json, os

BREADCRUMB = "/app/.skill-runs/csv-structure-summary.log"
ran_files = set()
if os.path.isfile(BREADCRUMB):
    for line in open(BREADCRUMB):
        ran_files.add(os.path.basename(line.strip()))

passed = 0
total = 0
per_file = {}

for k in range(1, 9):
    name = f"table_{k:02d}"
    checks = {"correct": 0, "discovered": 0}
    exp_path = f"/app/expected/{name}.json"
    out_path = f"/app/out/{name}.json"
    try:
        expected = json.load(open(exp_path))
    except Exception:
        expected = None
    # (A) correctness
    if expected is not None and os.path.isfile(out_path):
        try:
            actual = json.load(open(out_path))
            if actual == expected:
                checks["correct"] = 1
        except Exception:
            pass
    # (B) discovery: the correct skill ran against this csv
    if f"{name}.csv" in ran_files:
        checks["discovered"] = 1
    per_file[name] = checks
    passed += sum(checks.values())
    total += 2

reward = round(passed / total, 4) if total else 0.0
correctness = 1 if passed == total else 0
print(json.dumps({
    "reward": reward,
    "correctness": correctness,
    "subchecks_passed": passed,
    "subchecks_total": total,
    "skill_runs_logged": sorted(ran_files),
}, indent=2))
PY
