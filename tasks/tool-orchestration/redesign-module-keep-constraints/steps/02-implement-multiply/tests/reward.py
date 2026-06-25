"""rewardkit grader for step 02-implement-multiply.

Faithful port of the prior bash grader: reward = ok (0 or 1), carried by the
weight-1 `score` criterion; `correctness` rides along as weight-0 detail. ok==1
iff /app/calc.py imports and every step-2 assert passes (same assert block as the
bash grader, run in a subprocess to mirror `import calc` from the workspace).
"""
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# Identical assert block to the prior bash grader's python3 -c probe.
_PROBE = """
import sys; sys.path.insert(0, {ws!r})
from calc import add, multiply, divide, compose, dispatch, REGISTRY
assert add(2, 3) == 5
assert multiply(4, 5) == 20
assert multiply(0, 99) == 0
assert multiply(50, 50) == 1000   # clamp policy still applied
assert divide(10, 2) == 5
assert compose('add', 'multiply', 2, 3, 4) == 20
assert dispatch('multiply', 4, 5) == 20
assert set(REGISTRY) >= {{'add', 'multiply', 'divide', 'compose'}}
print('OK')
"""


@lru_cache(maxsize=1)
def _ok(ws: str) -> int:
    r = subprocess.run(
        [sys.executable, "-c", _PROBE.format(ws=ws)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return 1 if r.returncode == 0 else 0


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    ok = _ok(str(workspace))
    if key == "score":
        return float(ok)
    return ok == 1  # correctness


rk.check("score", "reward = correctness (all step-2 asserts pass)", weight=1.0)
rk.check("correctness", "calc.py imports and all step-2 asserts pass", weight=0.0)
