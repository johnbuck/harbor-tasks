"""rewardkit grader for step 03-revise-and-fix — the GRADED final step
(multi_step_reward_strategy="final"; only this counts).

Faithful port of the prior bash grader. Four weighted dimensions summed into the
weight-1 `score` criterion (reward, range 0..1):

  CLAMP MEMORY (0.40)  per-op 1/3 each: re-clamping add/multiply/subtract with the
      recalled [-1000,1000] bound (the harness-memory discriminator).
  FUNCTIONAL   (0.40)  6 checks, split evenly.
  CLEANUP      (0.12)  divide + compose removed (2 checks).
  REPLAN       (0.08)  PLAN.md updated (mentions subtract + apply_op; no ACTIVE
      divide(/compose( signature line).

The independent scratch-wipe assertion (a `clamp_note*` surviving in /tmp,
/var/tmp or /logs/agent VOIDs the result -> flat reward 0.0) is kept verbatim in
test.sh ahead of this scorer, exactly as the prior grader had it.

The functional/clamp/cleanup checks import /app/calc in a subprocess to mirror the
prior grader's `import calc` exactly (and avoid contaminating the grader process).
All per-dimension hits ride along as weight-0 detail.
"""
import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# Identical probe to the prior bash grader's python3 heredoc (import + checks).
_PROBE = r"""
import sys, json
sys.path.insert(0, {ws!r})

def check(fn):
    try:
        return bool(fn())
    except Exception:
        return False

calc = None
try:
    import calc as _calc
    calc = _calc
except Exception:
    calc = None

def c(fn):
    if calc is None:
        return False
    return check(fn)

clamp_add = c(lambda: calc.add(900, 900) == 1000 and calc.add(-900, -900) == -1000)
clamp_mul = c(lambda: calc.multiply(50, 50) == 1000 and calc.multiply(-50, 50) == -1000)
clamp_sub = c(lambda: calc.subtract(-900, 900) == -1000 and calc.subtract(900, -900) == 1000)

f_add = c(lambda: calc.add(2, 3) == 5 and calc.add(-1, 1) == 0)
f_mul = c(lambda: calc.multiply(4, 5) == 20 and calc.multiply(0, 99) == 0)
f_sub = c(lambda: calc.subtract(10, 3) == 7 and calc.subtract(0, 5) == -5)
f_dispatch = c(lambda: calc.apply_op('add', 2, 3) == 5
               and calc.apply_op('multiply', 4, 5) == 20
               and calc.apply_op('subtract', 10, 3) == 7)
def _raises():
    try:
        calc.apply_op('nope', 1, 1)
        return False
    except ValueError:
        return True
    except Exception:
        return False
f_raises = c(_raises)
f_names = c(lambda: sorted(calc.OP_NAMES) == ['add', 'multiply', 'subtract'])

clean_div = c(lambda: not hasattr(calc, 'divide'))
clean_comp = c(lambda: not hasattr(calc, 'compose'))

print(json.dumps({{
    "clamp_add": int(clamp_add), "clamp_mul": int(clamp_mul), "clamp_sub": int(clamp_sub),
    "f_add": int(f_add), "f_mul": int(f_mul), "f_sub": int(f_sub),
    "f_dispatch": int(f_dispatch), "f_raises": int(f_raises), "f_names": int(f_names),
    "clean_div": int(clean_div), "clean_comp": int(clean_comp),
}}))
"""


def _plan_ok(workspace: Path) -> int:
    # Mirrors the prior grader's bash PLAN.md check (line-based, case-insensitive).
    import re
    plan = workspace / "PLAN.md"
    if not plan.is_file():
        return 0
    p = plan.read_text(errors="replace").lower()
    has_subtract = "subtract" in p
    has_apply = "apply_op" in p
    active_sig = any(
        re.search(r"(divide|compose)\s*\(", line) for line in p.splitlines()
    )
    return 1 if (has_subtract and has_apply and not active_sig) else 0


@lru_cache(maxsize=1)
def _compute(ws: str):
    workspace = Path(ws)

    r = subprocess.run(
        [sys.executable, "-c", _PROBE.format(ws=ws)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )
    try:
        h = json.loads(r.stdout)
    except Exception:
        h = {k: 0 for k in (
            "clamp_add", "clamp_mul", "clamp_sub", "f_add", "f_mul", "f_sub",
            "f_dispatch", "f_raises", "f_names", "clean_div", "clean_comp")}

    clamp_hits = h["clamp_add"] + h["clamp_mul"] + h["clamp_sub"]
    clamp_score = 0.40 * (clamp_hits / 3.0)

    func_hits = (h["f_add"] + h["f_mul"] + h["f_sub"]
                 + h["f_dispatch"] + h["f_raises"] + h["f_names"])
    func_score = 0.40 * (func_hits / 6.0)

    cleanup_hits = h["clean_div"] + h["clean_comp"]
    cleanup_score = 0.12 * (cleanup_hits / 2.0)

    plan_ok = _plan_ok(workspace)
    replan_score = 0.08 * plan_ok

    reward = round(clamp_score + func_score + cleanup_score + replan_score, 4)
    all_pass = (clamp_hits == 3 and func_hits == 6
                and cleanup_hits == 2 and plan_ok == 1)
    return {
        "reward": reward,
        "correctness": 1 if all_pass else 0,
        "clamp_memory": round(clamp_score, 4),
        "functional": round(func_score, 4),
        "cleanup": round(cleanup_score, 4),
        "replan": float(replan_score),
        "clamp_ops_ok": clamp_hits,
        "functional_ok": func_hits,
        "cleanup_ok": cleanup_hits,
        "plan_replanned": plan_ok,
    }


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    r = _compute(str(workspace))
    if key == "score":
        return r["reward"]
    if key == "correctness":
        return r["correctness"] == 1
    return r[key]  # clamp_memory / functional / cleanup / replan (weight-0 detail)


rk.check("score", "reward = clamp(0.40) + functional(0.40) + cleanup(0.12) + replan(0.08)", weight=1.0)
# Weight-0 detail mirroring the prior grader's reward.json breakdown keys.
rk.check("clamp_memory", "CLAMP MEMORY dimension (0.40): re-clamp add/multiply/subtract", weight=0.0)
rk.check("functional", "FUNCTIONAL dimension (0.40): 6 spec checks", weight=0.0)
rk.check("cleanup", "CLEANUP dimension (0.12): divide + compose removed", weight=0.0)
rk.check("replan", "REPLAN dimension (0.08): PLAN.md updated", weight=0.0)
rk.check("correctness", "all checks pass (reward == 1.0)", weight=0.0)
