#!/bin/bash
# GRADED verifier for sub-agent-parallel-decompose-01 (60 prose word-problems).
#
# reward = correct / 60  — a NON-CLAMPED continuous base. Because solving all 60
# serially in one token-stream blows the 10-minute budget, a harness that grinds
# them one-by-one finishes only a prefix (base < 1.0); a harness that fans out to
# sub-agents (openclaw sessions_spawn / hermes delegate_task) completes far more
# in the same wall-clock and scores higher. The fan-out advantage IS the base
# reward — there is no separate clamped "parallelism bonus" to go inert.
#
# Concurrency is reported as a DIAGNOSTIC (not folded into reward), measured from
# the OUTPUT-FILE mtimes (OS wall-clock) — NOT from agent-self-reported
# timestamps, which a serial agent could fake. A tight mtime burst => genuine
# fan-out; mtimes spread evenly across the budget => serial.
#
# Answer key is /tests/answers.json (verifier-only — never in the agent
# container). Each answer is checked independently (no all-or-nothing collapse).
set -u
mkdir -p /logs/verifier
python3 - <<'PY' > /logs/verifier/reward.json
import json, os, re, glob

KEY = "/tests/answers.json"
OUT = "/app/out"
LOG = "/var/log/work.log"

key = {}
try:
    key = json.load(open(KEY))
except Exception:
    pass
total = len(key) or 60

def read_int(path):
    # Grade CONTENT, tolerate format: accept a bare "144", markdown ("**144**"),
    # or a short prose answer ("The answer is 144."). Take the LAST integer in the
    # file — in prose the answer trails the sentence, and a bare answer has only
    # one number — which avoids grabbing a stray leading token.
    try:
        s = open(path).read().strip()
    except Exception:
        return None
    nums = re.findall(r"-?\d+", s.replace(",", ""))
    return int(nums[-1]) if nums else None

correct = 0
written = 0
mtimes = []
for nn, ans in key.items():
    p = os.path.join(OUT, f"{nn}.txt")
    if os.path.exists(p):
        written += 1
        try:
            mtimes.append(os.path.getmtime(p))
        except OSError:
            pass
        if read_int(p) == ans:
            correct += 1

base = correct / total if total else 0.0

# --- concurrency diagnostic from OUTPUT mtimes (wall-clock) ---
# max files whose mtimes fall within any 3s sliding window.
max_burst = 0
span = 0.0
if mtimes:
    ms = sorted(mtimes)
    span = round(ms[-1] - ms[0], 2)
    j = 0
    for i in range(len(ms)):
        while ms[i] - ms[j] > 3.0:
            j += 1
        max_burst = max(max_burst, i - j + 1)

# --- secondary: self-reported BEGIN/END overlap from work.log (labelled) ---
self_reported_peak = 0
if os.path.exists(LOG):
    evs = []
    for line in open(LOG):
        m = re.match(r"^(\S+)\s+(BEGIN|END)\s+(\S+)", line.strip())
        if m:
            evs.append((m.group(1), 0 if m.group(2) == "BEGIN" else 1, m.group(3)))
    evs.sort(key=lambda e: (e[0], e[1]))
    openset, peak = set(), 0
    for _, kind, nn in evs:
        if kind == 0:
            openset.add(nn)
        else:
            openset.discard(nn)
        peak = max(peak, len(openset))
    self_reported_peak = peak

reward = round(base, 4)
correctness = 1 if correct == total else 0
print(json.dumps({
    "reward": reward,
    "correctness": correctness,
    "correct": correct,
    "total": total,
    "files_written": written,
    "mtime_burst_peak": max_burst,        # wall-clock concurrency proxy (diagnostic)
    "mtime_span_sec": span,
    "self_reported_peak": self_reported_peak,  # from work.log (agent-reported; advisory)
}))
PY
