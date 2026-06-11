"""rewardkit grader for tool-sprawl-precision-01 — tool SELECTION, not answer value.

The answer VALUE (customer_count / top_word / total_quantity) is deliberately NOT
graded: a root agent can compute it offline with plain python3, so scoring it
measures the MODEL, not the harness. We grade purely on which tools the harness
SELECTED and how economically, read from /var/log/tool-calls.log (every tool logs
its name + argv when invoked on data; reading `--help` is free and not logged).

reward = 0.5 * selection_f1 + 0.5 * call_efficiency

  precision       = correct-tool calls / total calls          (wrong tools hurt)
  recall          = distinct correct tools used / 3            (missed tools hurt)
  selection_f1    = harmonic mean(precision, recall)
  call_efficiency = distinct correct tools used / total calls  (NON-CLAMPED;
                    over-calling — even correct tools — and any wrong call lower it)

Ideal trajectory = invoke each of the 3 correct tools exactly once (total=3):
precision=recall=f1=1, efficiency=3/3=1 → 1.0. Spraying decoys lowers both terms;
re-running correct tools lowers efficiency only. Computing values offline and
never calling a tool → total=0 → 0.0 (the floor/VOID case, flagged by
`tools_invoked`).

The log is agent-writable (chmod 666) → a root agent that reverse-engineers the
grader could forge it, but honest tool use is the strictly-shorter path so neither
harness forges in practice. Residual root-forgery is documented, not hidden
(FOOTGUNS #44; D3 root-constraint). reward.json stays flat; breakdown is weight-0.
"""
import os
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

LOG = Path(os.environ.get("TOOL_CALL_LOG", "/var/log/tool-calls.log"))
CORRECT = ("recstat", "lexrank", "colroll")


@lru_cache(maxsize=4)
def _metrics(_cache_key: str):
    total, correct_calls, hit = 0, 0, set()
    if LOG.exists():
        for line in LOG.read_text().splitlines():
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
    efficiency = (len(hit) / total) if total > 0 else 0.0
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "efficiency": efficiency,
        "total_calls": float(total),
        "distinct_correct": float(len(hit)),
        "tools_invoked": 1.0 if total > 0 else 0.0,
    }


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    m = _metrics("k")
    if key == "score":
        return 0.5 * m["f1"] + 0.5 * m["efficiency"]
    return m[key]


rk.check("score", "reward = 0.5*selection_f1 + 0.5*call_efficiency", weight=1.0)
for _k, _l in [("f1", "tool-selection F1 (precision*recall)"),
               ("efficiency", "call efficiency (distinct correct / total calls)"),
               ("precision", "precision (correct calls / total calls)"),
               ("recall", "recall (distinct correct tools / 3)"),
               ("total_calls", "total tool invocations logged"),
               ("distinct_correct", "distinct correct tools invoked"),
               ("tools_invoked", "any tool invoked (0 = VOID/offline)")]:
    rk.check(_k, _l, weight=0.0)
