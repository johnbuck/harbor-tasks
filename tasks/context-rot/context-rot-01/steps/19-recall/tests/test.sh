#!/bin/bash
# CONTEXT-ROT recall scorer for MERIDIAN HALL.
# 12 paraphrased questions; each answer is matched on EXACTLY ONE line so a
# single blob listing every candidate cannot score (anti-dump). Needles sit at
# controlled conversational depth -> the per-position subscores expose the rot
# CURVE:
#   EARLY  (Q1-4, visits 2-6)   = primacy edge
#   MIDDLE (Q5-8, visits 8-12)  = lost-in-the-middle (rot-critical)
#   LATE   (Q9-12, visits 14-18)= recency edge
# A harness that suffers rot shows MIDDLE << EARLY,LATE; one that actively
# manages context flattens it. Headline reward = correct / 12.
#
# FORMAT-ROBUST (fixed 2026-06-01): the per-question line is found by, in order,
# (1) an enumerated line whose lead token is the question number ("N." / "N)" /
# "N:"), else (2) the Nth non-empty answer line (positional fallback). This
# accepts BOTH a numbered list and a bare one-answer-per-line list as equally
# valid formats -- the prior scorer REQUIRED the "N." prefix and scored a
# content-correct bare list as 0 (a false zero that fabricated discrimination).
# Anti-dump is preserved: each question still maps to a single distinct line.
mkdir -p /logs/verifier
# Archive the raw recall answer so a 0 is auditable: distinguishes "agent never
# persisted /app/answer.md" (a harness/plumbing VOID) from "answer present but
# wrong" (a genuine miss). See the 2026-06-02 ctx-02 false-zero finding.
cp /app/answer.md /logs/verifier/answer.md 2>/dev/null || true
python3 - <<'PY' > /logs/verifier/reward.json
import json, re

# (regex, bucket) in question order 1..12
PATTERNS = [
    (r"pitch[ -]?pine",                    "early"),
    (r"harcourt",                          "early"),
    (r"1788",                              "early"),
    (r"nickel[ -]?bronze",                 "early"),
    (r"aldhelm",                           "middle"),
    (r"crittall",                          "middle"),
    (r"white[ -]?oak",                     "middle"),
    (r"(14[,.]?000|fourteen[ -]thousand)", "middle"),
    (r"pugin",                             "late"),
    (r"flemish",                           "late"),
    (r"penrhyn",                           "late"),
    (r"gillett",                           "late"),
]

try:
    with open("/app/answer.md") as f:
        raw = f.read()
    lines = raw.split("\n")
except FileNotFoundError:
    raw = ""
    lines = []

# Positional answer lines: non-empty, excluding obvious preamble/header lines
# ("Here are my answers:", markdown headers) so a one-line preamble doesn't
# shift the bare-list mapping by one.
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
    s = re.sub(r"^\s*\d+\s*[.)\]:>-]\s*", "", s)  # leading enumerator
    s = re.sub(r"[*_`#>]", "", s)                  # markdown emphasis
    return s

def cell_for(n):  # 1-based
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
    "reward": reward, "correctness": corr, "facts": s,
    "early": buckets["early"], "middle": buckets["middle"], "late": buckets["late"],
    "answer_present": bool(nonempty), "answer_chars": len(raw),
    "status": "scored" if nonempty else "no_answer_file",
}))
PY
