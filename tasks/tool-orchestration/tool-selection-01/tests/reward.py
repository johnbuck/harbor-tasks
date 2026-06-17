"""rewardkit grader for tool-selection-01 — answer correctness + tool-selection F1.

reward = 0.5 * answer_fraction + 0.5 * tool_f1, where answer_fraction = correct/3
over the 3 sub-answers and tool_f1 is the harmonic mean of precision (fraction of
logged tool calls that were to one of the 3 correct tools) and recall (how many of
the 3 correct tools were invoked). The SCORED tool_f1 reads the root-owned
/logs/tool-calls.log (TRUSTED_LOG), which the tool wrappers populate alongside the
agent-facing /var/log copy; an honest tool trajectory therefore scores tool_f1=1.0.

Blend isn't an additive criterion-mean, so the exact reward lives in a weight-1
`score` criterion; the 3 answer checks + the F1 ride along as weight-0 detail.
(NOTE: the agent runs as root, so even the trusted channel is forgeable by a root
principal; scoring the wrappers' own channel rather than the agent-facing log
raises the bar against a NON-root forger. See FOOTGUNS #44.)
"""
import json
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

LOG = Path("/var/log/tool-calls.log")          # agent-writable: forgeable -> diagnostic only
TRUSTED_LOG = Path("/logs/tool-calls.log")     # root-only harness channel: the SCORED source
CORRECT = ("jsonl-count", "semver-max", "money-sum")
EXPECTED = {"record_count": 6, "latest_version": "1.10.10", "total_cents": 2100}


@lru_cache(maxsize=4)
def _metrics(workspace_str: str):
    got = {}
    p = Path(workspace_str) / "answer.json"
    if p.exists():
        try:
            got = json.loads(p.read_text(errors="replace"))
        except Exception:
            got = {}
    def _as_int(x):
        try:
            return int(round(float(x)))
        except (TypeError, ValueError):
            return None
    rc = _as_int(got.get("record_count")) == EXPECTED["record_count"]
    lv = str(got.get("latest_version", "")).strip() == EXPECTED["latest_version"]
    tc = _as_int(got.get("total_cents")) == EXPECTED["total_cents"]
    answer_fraction = sum([rc, lv, tc]) / 3.0

    def _f1(logpath):
        total, correct_calls, hit = 0, 0, set()
        if logpath.exists():
            for line in logpath.read_text(errors="replace").splitlines():
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
        return 0.0 if (precision + recall) == 0 else 2 * precision * recall / (precision + recall)

    # The SCORED tool_f1 reads the root-only trusted channel; the agent-writable
    # log is forgeable, so it is reported only as a weight-0 diagnostic.
    f1 = _f1(TRUSTED_LOG)
    f1_diag = _f1(LOG)
    return {"rc": rc, "lv": lv, "tc": tc, "answer_fraction": answer_fraction,
            "f1": f1, "f1_diag": f1_diag}


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


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "answer.json"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)
