#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
#
# Nine independent sub-checks across four discrimination dimensions:
#   functional (5): add, multiply, subtract, apply_op-dispatch, apply_op-raises
#   constant   (1): OP_NAMES == ["add","multiply","subtract"]
#   cleanup    (1): divide/compose REMOVED from calc.py (re-plan, not blind exec)
#   replan     (1): PLAN.md updated — mentions subtract+apply_op, no divide/compose
#   MEMORY     (1): subtract honours the kickoff CLAMP policy ([-1000,1000]).
#                   The harness-memory discriminator: the clamp VALUE was stated
#                   only in step 1 and is NOT restated in REVISION.md (which only
#                   says "follow the same policy as add/multiply"). A harness that
#                   retained the early decision clamps subtract; one that
#                   re-derived the module from REVISION.md alone ships an
#                   un-clamped subtract and loses this point — while still passing
#                   the plain subtract(10,3)==7 check.
#
#   reward = matched / 9   (continuous gradient — a harness that blindly
#   executes the stale 4-fn plan leaves divide/compose behind and/or a stale
#   PLAN.md, shaving reward; one that re-plans cleanly AND remembers the clamp
#   policy scores higher).
#   correctness = 1 only if all 9 sub-checks pass.
set -u
mkdir -p /logs/verifier
s=0

# --- functional + constant sub-checks (run each independently) ---
chk() {
    python3 - <<PY >/dev/null 2>&1
import sys; sys.path.insert(0, '/app')
import importlib, calc
importlib.reload(calc)
$1
PY
}

chk "assert calc.add(2,3)==5 and calc.add(-1,1)==0"                      && s=$((s+1))   # add
chk "assert calc.multiply(4,5)==20 and calc.multiply(0,99)==0"          && s=$((s+1))   # multiply
chk "assert calc.subtract(10,3)==7 and calc.subtract(0,5)==-5"          && s=$((s+1))   # subtract
chk "assert calc.subtract(-900,900)==-1000 and calc.subtract(900,-900)==1000" && s=$((s+1))  # MEMORY: subtract clamps per the kickoff policy
chk "assert calc.apply_op('add',2,3)==5 and calc.apply_op('multiply',4,5)==20 and calc.apply_op('subtract',10,3)==7" && s=$((s+1))  # dispatch
chk "
try:
    calc.apply_op('nope',1,1); raise SystemExit(1)
except ValueError:
    pass"                                                                && s=$((s+1))   # raises
chk "assert list(calc.OP_NAMES)==['add','multiply','subtract']"          && s=$((s+1))   # OP_NAMES

# --- cleanup sub-check: divide/compose must be gone ---
chk "assert not hasattr(calc,'divide') and not hasattr(calc,'compose')"  && s=$((s+1))   # cleanup

# --- replan sub-check: PLAN.md reflects the revised spec ---
# Positive signal only: the revised plan must mention BOTH new requirements
# (subtract + apply_op), and must NOT list divide/compose as ACTIVE planned
# functions (a "scrapped divide/compose" note is fine — documenting the removal
# is good re-planning, so we only reject a divide(/compose( signature line). The
# actual removal of divide/compose from the CODE is graded independently above.
plan_ok=0
if [ -f /app/PLAN.md ]; then
    p=$(tr '[:upper:]' '[:lower:]' < /app/PLAN.md)
    if echo "$p" | grep -q subtract && echo "$p" | grep -q apply_op \
       && ! echo "$p" | grep -qE '(divide|compose)[[:space:]]*\('; then
        plan_ok=1
    fi
fi
[ "$plan_ok" -eq 1 ] && s=$((s+1))

reward=$(python3 -c "print(round($s / 9.0, 4))")
correctness=$(python3 -c "print(1 if $s == 9 else 0)")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "matched": ${s}, "max": 9, "plan_replanned": ${plan_ok}}
EOF
