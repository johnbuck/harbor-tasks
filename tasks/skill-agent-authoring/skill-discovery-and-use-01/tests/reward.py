"""rewardkit grader for skill-discovery-and-use-01.

8 files x 2 independent binary sub-checks = 16 criteria, equal weight:
  (A) table_XX correct    — /app/out/table_XX.json matches the canonical
      shape report RECOMPUTED from /app/data/table_XX.csv at grade time (this
      requires the correct skill's `--null=empty` mode; the default mode and the
      colliding decoys produce a near-miss that fails here).
  (B) table_XX discovered — the correct skill (tabular-shape-report) actually
      read this file, proven by a breadcrumb line `<file> <sha256-of-bytes>` in
      /app/.skill-runs/tabular-shape-report.log whose hash the grader re-derives
      from /app/data/table_XX.csv. Echoing filenames no longer suffices — the
      hash must match the real bytes.

reward = passed_subchecks / 16 (weighted_mean of 16 equal-weight binary
criteria → identical to the previous bash grader's `passed/16`). The per-file
breakdown now lands in reward-details.json (visible in `harbor view`) instead
of being discarded to satisfy Harbor's flat-scalar reward.json rule (FOOTGUNS
#38) — reward.json stays {"reward": <float>}.

LEAK-PROOF: the expected answers are NOT materialized anywhere the agent can
read. This grader derives them from the SAME public input the agent got
(/app/data) using the SAME dtype/null logic the correct skill documents, so the
oracle (which runs the real skill with `--null=empty`) scores 16/16 and a
copy-the-answer-key cheat has nothing to copy.
"""

import csv
import hashlib
import json
from pathlib import Path

import rewardkit as rk

BREADCRUMB = ".skill-runs/tabular-shape-report.log"
CORRECT_SKILL = "tabular-shape-report"

# Brute-force-sweep gate. Discovery credit proves the agent IDENTIFIED the right
# skill — not that it ran every skill on every file and let the correct one log a
# breadcrumb as a side effect. Every skill now drops its own
# .skill-runs/<name>.log breadcrumb when invoked; a "run all 13 on all 8" sweep
# therefore leaves a fleet of busy DECOY logs. If that signature is present, the
# discovery half is denied (the agent did not discover, it brute-forced).
SWEEP_DECOY_FILES = 6   # a decoy log covering >= this many distinct files is "busy"
SWEEP_BUSY_DECOYS = 6   # this many busy decoy skills == a brute-force sweep


def _is_brute_sweep(workspace: Path) -> bool:
    runs = workspace / ".skill-runs"
    if not runs.is_dir():
        return False
    busy = 0
    for log in runs.glob("*.log"):
        if log.stem == CORRECT_SKILL:
            continue
        try:
            files = {ln.split()[0] for ln in log.read_text().splitlines() if ln.split()}
        except OSError:
            continue
        if len(files) >= SWEEP_DECOY_FILES:
            busy += 1
    return busy >= SWEEP_BUSY_DECOYS


def _infer_dtype(values):
    seen = set()
    for v in values:
        if v == "":
            continue
        try:
            int(v); seen.add("int"); continue
        except ValueError:
            pass
        try:
            float(v); seen.add("float"); continue
        except ValueError:
            pass
        seen.add("str")
    if not seen:
        return "unknown"
    if seen == {"int"}:
        return "int"
    if seen <= {"int", "float"}:
        return "float"
    return "str"


def _summary(csv_path: Path):
    """Canonical shape report — mirrors tabular-shape-report/run.py --null=empty."""
    rows = list(csv.reader(csv_path.open(newline="")))
    if not rows:
        return {"rows": 0, "columns": []}
    header, *data = rows
    cols = []
    for i, name in enumerate(header):
        vals = [r[i] if i < len(r) else "" for r in data]
        cols.append({"name": name, "dtype": _infer_dtype(vals),
                     "nulls": sum(1 for v in vals if v == "")})
    return {"rows": len(data), "columns": cols}


@rk.criterion(description="table_{k:02d} correct")
def table_correct(workspace: Path, k: int) -> bool:
    out = workspace / "out" / f"table_{k:02d}.json"
    src = workspace / "data" / f"table_{k:02d}.csv"
    if not out.is_file() or not src.is_file():
        return False
    try:
        return json.loads(out.read_text()) == _summary(src)
    except Exception:
        return False


@rk.criterion(description="table_{k:02d} discovered (correct skill ran)")
def table_discovered(workspace: Path, k: int) -> bool:
    bc = workspace / BREADCRUMB
    src = workspace / "data" / f"table_{k:02d}.csv"
    if not bc.is_file() or not src.is_file():
        return False
    # A brute-force "run every skill on every file" sweep banks the correct
    # skill's breadcrumb as a side effect without ever DISCOVERING it. Deny
    # discovery credit when that decoy-sweep signature is present.
    if _is_brute_sweep(workspace):
        return False
    want = f"table_{k:02d}.csv {hashlib.sha256(src.read_bytes()).hexdigest()}"
    lines = {line.strip() for line in bc.read_text().splitlines() if line.strip()}
    return want in lines


for _k in range(1, 9):
    rk.table_correct(_k)
    rk.table_discovered(_k)
