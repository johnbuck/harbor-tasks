#!/bin/bash
# Graded verifier: blends answer-correctness with tool-selection precision/recall.
# Deterministic (no LLM judge). All counting is done in Python to avoid grep
# exit-code artifacts and to keep reward.json a clean flat dict of scalars.
#
#   answer_fraction = (# of the 3 answer fields correct) / 3
#   tool_f1         = harmonic mean of tool precision + recall over the 3 correct
#                     tools, read from /var/log/tool-calls.log
#   reward = 0.5 * answer_fraction + 0.5 * tool_f1
#
# Additive (not multiplied) so the reward is a continuous gradient: a wrong
# sub-answer (e.g. reaching for the lexicographic-max decoy) or a sloppy tool
# call each shave a measurable fraction. correctness=1 only when all three
# answers are right AND tool selection is perfect (f1==1).
set -u
mkdir -p /logs/verifier

python3 - <<'PY'
import json, os, re

ANS = "/app/answer.json"
LOG = "/var/log/tool-calls.log"
CORRECT = ("jsonl-count", "semver-max", "money-sum")
EXPECTED = {"record_count": 6, "latest_version": "1.10.2", "total_cents": 2100}

# --- answer correctness (3 sub-checks) ---
ans_ok = 0
got = {}
if os.path.exists(ANS):
    try:
        got = json.load(open(ANS))
    except Exception:
        got = {}
if got.get("record_count") == EXPECTED["record_count"]:
    ans_ok += 1
if str(got.get("latest_version", "")).strip() == EXPECTED["latest_version"]:
    ans_ok += 1
if got.get("total_cents") == EXPECTED["total_cents"]:
    ans_ok += 1
answer_fraction = ans_ok / 3.0

# --- tool selection from the invocation log ---
total = 0
correct_calls = 0
hit_tools = set()
if os.path.exists(LOG):
    for line in open(LOG):
        line = line.strip()
        if not line:
            continue
        # format: "<iso-timestamp> <toolname> <args...>"
        parts = line.split(None, 2)
        if len(parts) < 2:
            continue
        name = parts[1]
        total += 1
        if name in CORRECT:
            correct_calls += 1
            hit_tools.add(name)

precision = (correct_calls / total) if total > 0 else 0.0
recall = len(hit_tools) / len(CORRECT)
tool_f1 = 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)

reward = round(0.5 * answer_fraction + 0.5 * tool_f1, 4)
correctness = 1 if (ans_ok == 3 and abs(tool_f1 - 1.0) < 1e-9) else 0

out = {
    "reward": reward,
    "correctness": correctness,
    "answer_fraction": round(answer_fraction, 4),
    "answers_correct": ans_ok,
    "tool_precision": round(precision, 4),
    "tool_recall": round(recall, 4),
    "tool_f1": round(tool_f1, 4),
    "tool_calls_total": total,
    "tool_calls_correct": correct_calls,
}
with open("/logs/verifier/reward.json", "w") as f:
    json.dump(out, f)
print(json.dumps(out))
PY
