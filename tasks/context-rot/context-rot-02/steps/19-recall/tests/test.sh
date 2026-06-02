#!/bin/bash
# CONTEXT-ROT MULTI-HOP scorer for WESTMARCH PRIORY.
# 8 two-hop chains; each final answer matched on EXACTLY ONE line (anti-dump).
# Chains bucketed by depth -> the subscores expose the rot curve:
#   EARLY  (Q1-2, both hops visits 2-6)   = primacy-protected
#   MIDDLE (Q3-5, both hops visits 8-12)  = lost-in-the-middle, rot-critical
#   LATE   (Q6-8, both hops visits 14-18) = recency-protected
# Rot breaks a chain if EITHER hop is lost, so MIDDLE << EARLY,LATE signals rot;
# a harness with active context management flattens it. Reward = correct / 8.
#
# FORMAT-ROBUST (fixed 2026-06-01): per-question line = an enumerated "N." line
# if present, else the Nth non-empty answer line (positional). Accepts a numbered
# OR a bare one-answer-per-line list. The prior scorer REQUIRED "N." and scored a
# content-correct bare list as 0 -- on the first real run hermes wrote all 8
# chains correctly as a bare list and was scored 0.0 (a false zero that
# fabricated an 0.875-vs-0.0 "gap"). Anti-dump preserved: one line per question.
mkdir -p /logs/verifier
# Archive the raw recall answer so a 0 is auditable: distinguishes "agent never
# persisted /app/answer.md" (a harness/plumbing VOID) from "answer present but
# wrong" (a genuine miss). 2026-06-02: hermes solved all 8 chains but its staged
# diff-write never landed in /app -> scored 0; openclaw's direct write landed -> 0.875.
cp /app/answer.md /logs/verifier/answer.md 2>/dev/null || true
python3 - <<'PY' > /logs/verifier/reward.json
import json, re

# (regex, bucket) in question order 1..8 (final hop of each chain)
PATTERNS = [
    (r"lyon",                   "early"),
    (r"jackfield",              "early"),
    (r"thames",                 "middle"),
    (r"(saint|st\.?)[ -]?luke", "middle"),
    (r"durham",                 "middle"),
    (r"hereford",               "late"),
    (r"loughborough",           "late"),
    (r"latvia",                 "late"),
]

try:
    with open("/app/answer.md") as f:
        raw = f.read()
    lines = raw.split("\n")
except FileNotFoundError:
    raw = ""
    lines = []

def is_preamble(ln):
    s = ln.strip()
    if s.startswith("#"):
        return True
    if re.match(r"(?i)^(here|below|the following|answers?|my answers?)\b.*:\s*$", s):
        return True
    return False

nonempty = [ln for ln in lines if ln.strip() and not is_preamble(ln)]

def enum_line(n):
    pat = re.compile(rf"^\s*{n}\s*[.)\]:>-]")
    for ln in lines:
        if pat.match(ln):
            return ln
    return None

def strip_marks(s):
    s = re.sub(r"^\s*\d+\s*[.)\]:>-]\s*", "", s)
    s = re.sub(r"[*_`#>]", "", s)
    return s

def cell_for(n):
    el = enum_line(n)
    if el is not None:
        return strip_marks(el)
    if n - 1 < len(nonempty):
        return strip_marks(nonempty[n - 1])
    return ""

buckets = {"early": 0, "middle": 0, "late": 0}
for i, (pat, b) in enumerate(PATTERNS, start=1):
    if re.search(pat, cell_for(i), re.I):
        buckets[b] += 1

s = sum(buckets.values())
total = len(PATTERNS)
reward = round(s / total, 4) if total else 0.0
corr = 1 if s == total else 0
print(json.dumps({
    "reward": reward, "correctness": corr, "chains": s,
    "early": buckets["early"], "middle": buckets["middle"], "late": buckets["late"],
    "answer_present": bool(nonempty), "answer_chars": len(raw),
    "status": "scored" if nonempty else "no_answer_file",
}))
PY
