"""rewardkit grader for tool-selection-01 — answer correctness + tool-selection F1.

reward = 0.5 * answer_fraction + 0.5 * tool_f1, where answer_fraction = correct/3
over the 3 sub-answers and tool_f1 is the harmonic mean of precision (fraction of
logged tool calls that were to one of the 3 correct tools) and recall (how many of
the 3 correct tools were invoked), read from /var/log/tool-calls.log. Same formula
+ comparisons as the prior bash grader.

Blend isn't an additive criterion-mean, so the exact reward lives in a weight-1
`score` criterion; the 3 answer checks + the F1 ride along as weight-0 detail.
(NOTE: tool_f1 is read from an agent-writable log — an adversarial agent could
forge it, but honest harnesses produce a genuine trace; see FOOTGUNS #44.)
"""
import json
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

LOG = Path("/var/log/tool-calls.log")
CORRECT = ("jsonl-count", "semver-max", "money-sum")
EXPECTED = {"record_count": 6, "latest_version": "1.10.10", "total_cents": 2100}


@lru_cache(maxsize=4)
def _metrics(workspace_str: str):
    got = {}
    p = Path(workspace_str) / "answer.json"
    if p.exists():
        try:
            got = json.loads(p.read_text())
        except Exception:
            got = {}
    rc = got.get("record_count") == EXPECTED["record_count"]
    lv = str(got.get("latest_version", "")).strip() == EXPECTED["latest_version"]
    tc = got.get("total_cents") == EXPECTED["total_cents"]
    answer_fraction = sum([rc, lv, tc]) / 3.0

    total, correct_calls, hit = 0, 0, set()
    if LOG.exists():
        for line in LOG.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 2)  # "<iso-ts> <toolname> <args...>"
            if len(parts) < 2:
                continue
            total += 1
            if parts[1] in CORRECT:
                correct_calls += 1
                hit.add(parts[1])
    precision = (correct_calls / total) if total > 0 else 0.0
    recall = len(hit) / len(CORRECT)
    f1 = 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)
    return {"rc": rc, "lv": lv, "tc": tc, "answer_fraction": answer_fraction, "f1": f1}


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    m = _metrics(str(workspace))
    if key == "score":
        return 0.5 * m["answer_fraction"] + 0.5 * m["f1"]
    if key == "f1":
        return m["f1"]
    return m[key]


rk.check("score", "reward = 0.5*answer_fraction + 0.5*tool_f1", weight=1.0)
for _k, _l in [("rc", "answer: record_count correct"),
               ("lv", "answer: latest_version correct"),
               ("tc", "answer: total_cents correct"),
               ("f1", "tool-selection F1 (precision*recall)")]:
    rk.check(_k, _l, weight=0.0)
