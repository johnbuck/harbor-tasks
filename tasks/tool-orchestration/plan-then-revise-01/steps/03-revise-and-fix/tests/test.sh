#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
#
# Four weighted dimensions (reward = weighted sum, range 0..1):
#
#   CLAMP MEMORY  (0.40)  the harness-memory discriminator. The clamp bound
#       value [-1000,1000] was stated ONLY in the step-1/2 conversation; it is
#       absent from this step's instruction AND from the on-disk module (setup.sh
#       stripped _clamp and shipped add/multiply/divide UN-CLAMPED). Re-applying
#       the clamp to add, multiply AND subtract therefore requires RECALLING that
#       value, not reading it off disk. Graded per-op (1/3 each). A harness that
#       rebuilt the module from the revision message alone (no retained memory)
#       ships everything un-clamped and scores 0 on this whole dimension while
#       still passing the plain functional checks below -> reward caps near 0.60.
#
#   FUNCTIONAL    (0.40)  the final spec exists and works: add/multiply/subtract
#       base values, apply_op name-dispatch, apply_op raises on unknown,
#       OP_NAMES == ["add","multiply","subtract"]. (6 checks, weight split evenly.)
#
#   CLEANUP       (0.12)  divide and compose REMOVED (revise, not blind append).
#
#   REPLAN        (0.08)  PLAN.md updated to the revised design (mentions subtract
#       + apply_op; no ACTIVE divide(/compose( signature line).
#
#   correctness = 1 only if every check passes (reward == 1.0).
set -u
mkdir -p /logs/verifier

# Independent scratch-wipe assertion (workdir/setup.sh sources the canonical wipe;
# multi_step treats its failure as only a warning). The clamp bound is a memory
# discriminator, so a stashed note in scratch would void the result — fail loudly
# (flat reward 0.0) if one survived.
if find /tmp /var/tmp /logs/agent -maxdepth 3 -name 'clamp_note*' 2>/dev/null | grep -q .; then
    echo '{"reward": 0.0}' > /logs/verifier/reward.json
    echo "WIPE ASSERTION FAILED: scratch survived the pre-revise wipe" >&2
    exit 1
fi

if [ -f /app/PLAN.md ]; then
    p=$(tr '[:upper:]' '[:lower:]' < /app/PLAN.md)
    if echo "$p" | grep -q subtract && echo "$p" | grep -q apply_op \
       && ! echo "$p" | grep -qE '(divide|compose)[[:space:]]*\('; then
        plan_ok=1
    else
        plan_ok=0
    fi
else
    plan_ok=0
fi

PLAN_OK="$plan_ok" python3 - <<'PY'
import os, sys, json
sys.path.insert(0, '/app')

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

# --- CLAMP MEMORY (0.40) : per-op, 1/3 each ---
clamp_add = c(lambda: calc.add(900, 900) == 1000 and calc.add(-900, -900) == -1000)
clamp_mul = c(lambda: calc.multiply(50, 50) == 1000 and calc.multiply(-50, 50) == -1000)
clamp_sub = c(lambda: calc.subtract(-900, 900) == -1000 and calc.subtract(900, -900) == 1000)
clamp_hits = clamp_add + clamp_mul + clamp_sub
clamp_score = 0.40 * (clamp_hits / 3.0)

# --- FUNCTIONAL (0.40) : 6 checks ---
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
func_hits = f_add + f_mul + f_sub + f_dispatch + f_raises + f_names
func_score = 0.40 * (func_hits / 6.0)

# --- CLEANUP (0.12) : divide + compose gone ---
clean_div = c(lambda: not hasattr(calc, 'divide'))
clean_comp = c(lambda: not hasattr(calc, 'compose'))
cleanup_hits = clean_div + clean_comp
cleanup_score = 0.12 * (cleanup_hits / 2.0)

# --- REPLAN (0.08) : PLAN.md (computed in bash) ---
plan_ok = 1 if os.environ.get('PLAN_OK') == '1' else 0
replan_score = 0.08 * plan_ok

reward = round(clamp_score + func_score + cleanup_score + replan_score, 4)
all_pass = (clamp_hits == 3 and func_hits == 6 and cleanup_hits == 2 and plan_ok == 1)
correctness = 1 if all_pass else 0

out = {
    "reward": reward,
    "correctness": correctness,
    "clamp_memory": round(clamp_score, 4),
    "functional": round(func_score, 4),
    "cleanup": round(cleanup_score, 4),
    "replan": float(replan_score),
    "clamp_ops_ok": clamp_hits,
    "functional_ok": func_hits,
    "cleanup_ok": cleanup_hits,
    "plan_replanned": plan_ok,
}
with open('/logs/verifier/reward.json', 'w') as fh:
    json.dump(out, fh)
print(json.dumps(out))
PY
