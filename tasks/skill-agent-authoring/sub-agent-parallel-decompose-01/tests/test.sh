#!/bin/bash
# Graded verifier (rewardkit): reward = correct/60 over the prose word-problems,
# one criterion per problem (answer key in /tests/answers.json, verifier-only).
# Shared-mode grader; rewardkit baked in the base. The fan-out concurrency
# DIAGNOSTIC (not part of reward) is computed into a sidecar so it doesn't pollute
# reward.json. Per-problem breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json

# --- concurrency diagnostic (advisory; NOT scored) -> sidecar ----------------
python3 - <<'PY'
import json, os, re, glob
OUT, LOG = "/app/out", "/var/log/work.log"
mtimes = []
for p in glob.glob(os.path.join(OUT, "*.txt")):
    try:
        mtimes.append(os.path.getmtime(p))
    except OSError:
        pass
max_burst, span = 0, 0.0
if mtimes:
    ms = sorted(mtimes)
    span = round(ms[-1] - ms[0], 2)
    j = 0
    for i in range(len(ms)):                 # max files within any 3s window
        while ms[i] - ms[j] > 3.0:
            j += 1
        max_burst = max(max_burst, i - j + 1)
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
        openset.add(nn) if kind == 0 else openset.discard(nn)
        peak = max(peak, len(openset))
    self_reported_peak = peak
json.dump({"mtime_burst_peak": max_burst, "mtime_span_sec": span,
           "self_reported_peak": self_reported_peak},
          open("/logs/verifier/concurrency.json", "w"))
PY
