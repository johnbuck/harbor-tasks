"""rewardkit grader for sub-agent-parallel-decompose-01 — 60 prose word-problems.

reward = correct/60. Each /app/out/<nn>.txt is graded CONTENT-tolerant (last integer
in the file, comma-stripped) against the answer key /tests/answers.json (verifier-only,
never in the agent container). One criterion per problem → weighted_mean = correct/60.

There is NO concurrency score. Delegation is reflected ONLY through correct/60: a
serial harness that times out writes fewer outputs -> lower base. test.sh additionally
emits ADVISORY-ONLY, explicitly-gameable mtime/work.log figures to
/logs/verifier/reward-details.json -- never into reward.json.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

KEY = Path("/tests/answers.json")


@lru_cache(maxsize=1)
def _answers() -> tuple:
    # Narrow + explicit: a missing/corrupt key registers zero criteria (so the
    # grader's crash fallback in test.sh emits a flat reward 0.0) rather than
    # masking an unrelated bug behind a bare except.
    try:
        return tuple(sorted(json.loads(KEY.read_text()).items()))
    except (OSError, ValueError) as exc:
        print(f"answers.json unreadable ({exc}); registering 0 criteria")
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
