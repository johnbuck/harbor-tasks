"""rewardkit grader for sub-agent-parallel-decompose-01 — 60 prose word-problems.

reward = correct/60. Each /app/out/<nn>.txt is graded CONTENT-tolerant (last integer
in the file, comma-stripped) against the answer key /tests/answers.json (verifier-only,
never in the agent container). One criterion per problem → weighted_mean = correct/60.

The fan-out concurrency DIAGNOSTIC (mtime burst, work.log overlap) is not part of the
reward; test.sh computes it into a sidecar /logs/verifier/concurrency.json so the
delegation evidence survives without polluting reward.json.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

KEY = Path("/tests/answers.json")


@lru_cache(maxsize=1)
def _answers() -> tuple:
    try:
        return tuple(sorted(json.loads(KEY.read_text()).items()))
    except Exception:
        return ()


def _read_int(path: Path):
    """Last integer in the file (tolerates bare '144', '**144**', prose)."""
    try:
        s = path.read_text().strip()
    except Exception:
        return None
    nums = re.findall(r"-?\d+", s.replace(",", ""))
    return int(nums[-1]) if nums else None


@rk.criterion(description="problem {nn} correct")
def problem(workspace: Path, nn: str, ans: int) -> bool:
    return _read_int(workspace / "out" / f"{nn}.txt") == ans


for _nn, _ans in _answers():
    rk.problem(_nn, _ans)
