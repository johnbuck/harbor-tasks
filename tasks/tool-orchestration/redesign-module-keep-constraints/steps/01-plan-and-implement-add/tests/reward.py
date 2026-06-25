"""rewardkit grader for step 01-plan-and-implement-add.

Faithful port of the prior bash grader: reward = (plan_ok + ok) / 2.0, carried by
the weight-1 `score` criterion. `correctness` (ok) and `plan_written` (plan_ok)
ride along as weight-0 detail. ok==1 iff /app/calc.py imports and every step-1
functional assert passes (same assert block as the bash grader, run in a
subprocess to mirror `import calc` from the workspace); plan_ok==1 iff
/app/PLAN.md exists and is non-empty (`-f` && `-s`).
"""
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# Identical assert block to the prior bash grader's python3 -c probe.
_PROBE = """
import sys; sys.path.insert(0, {ws!r})
from calc import add, divide, dispatch
assert add(2, 3) == 5
assert add(-1, 1) == 0
assert add(900, 900) == 1000     # clamp policy (upper)
assert add(-900, -900) == -1000  # clamp policy (lower)
assert divide(10, 2) == 5
assert divide(5000, 2) == 1000   # divide clamps too
try:
    divide(1, 0); raise SystemExit(1)
except ValueError:
    pass
assert dispatch('add', 2, 3) == 5
try:
    dispatch('nope', 1, 1); raise SystemExit(1)
except ValueError:
    pass
print('OK')
"""


@lru_cache(maxsize=1)
def _compute(ws: str):
    workspace = Path(ws)
    plan = workspace / "PLAN.md"
    plan_ok = 1 if (plan.is_file() and plan.stat().st_size > 0) else 0

    ok = 0
    if (workspace / "calc.py").is_file():
        r = subprocess.run(
            [sys.executable, "-c", _PROBE.format(ws=str(workspace))],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ok = 1 if r.returncode == 0 else 0

    reward = (plan_ok + ok) / 2.0
    return {"reward": reward, "ok": ok, "plan_ok": plan_ok}


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    r = _compute(str(workspace))
    if key == "score":
        return r["reward"]
    if key == "correctness":
        return r["ok"] == 1
    return r["plan_ok"] == 1  # plan_written


rk.check("score", "reward = (plan_written + correctness) / 2", weight=1.0)
rk.check("correctness", "calc.py imports and all step-1 asserts pass", weight=0.0)
rk.check("plan_written", "PLAN.md exists and is non-empty", weight=0.0)
