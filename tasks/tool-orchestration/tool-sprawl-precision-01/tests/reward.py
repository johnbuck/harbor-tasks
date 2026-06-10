"""rewardkit grader for tool-sprawl-precision-01 — answer correctness + tool F1.

reward = 0.5 * answer_fraction + 0.5 * tool_f1 over 60 candidate tools where exactly
3 solve the task. answer_fraction = correct/3; tool_f1 is precision*recall over the
3 correct tools, read from /var/log/tool-calls.log. Same formula + (string)
comparisons as the prior bash grader.

Blend → weight-1 `score` criterion holds the exact reward; 3 answer checks + F1 are
weight-0 detail. (PROVEN efficiency discriminator. tool_f1 reads an agent-writable
log — forgeable by an adversary but genuine for honest harnesses; see FOOTGUNS #44.)
"""
import json
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

LOG = Path("/var/log/tool-calls.log")
CORRECT = ("csv-row-count", "word-tally", "json-key-sum")
# answers compared as strings (matches the prior grader's `[ "$x" = "7" ]`).
EXPECTED = {"customer_count": "7", "top_word": "the", "total_quantity": "19"}


@lru_cache(maxsize=4)
def _metrics(workspace_str: str):
    got = {}
    p = Path(workspace_str) / "answer.json"
    if p.exists():
        try:
            got = json.loads(p.read_text())
        except Exception:
            got = {}
    cc = str(got.get("customer_count")) == EXPECTED["customer_count"]
    tw = str(got.get("top_word", "")).lower() == EXPECTED["top_word"]
    tq = str(got.get("total_quantity")) == EXPECTED["total_quantity"]
    answer_fraction = sum([cc, tw, tq]) / 3.0

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
    return {"cc": cc, "tw": tw, "tq": tq, "answer_fraction": answer_fraction, "f1": f1}


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    m = _metrics(str(workspace))
    if key == "score":
        return 0.5 * m["answer_fraction"] + 0.5 * m["f1"]
    if key == "f1":
        return m["f1"]
    return m[key]


rk.check("score", "reward = 0.5*answer_fraction + 0.5*tool_f1", weight=1.0)
for _k, _l in [("cc", "answer: customer_count correct"),
               ("tw", "answer: top_word correct"),
               ("tq", "answer: total_quantity correct"),
               ("f1", "tool-selection F1 (precision*recall)")]:
    rk.check(_k, _l, weight=0.0)
