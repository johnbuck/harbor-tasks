#!/bin/bash
# Step-3 baseline. We overwrite /app/calc.py and /app/PLAN.md to a single,
# deterministic "current state of the repo" so grading does not depend on the
# exact bytes the agent produced in steps 1-2. Two things matter here:
#
#  1. The shared _clamp helper and the project-wide bound VALUE are GONE from
#     disk, and add/multiply/divide are shipped UN-clamped. The numeric bound
#     was stated only in the step-1 (and step-2) conversation; it is NOT written
#     anywhere the step-3 agent can read it. So re-applying the
#     clamp on the final module requires RECALLING that value, not reading it off
#     disk -- this is the harness-memory discriminator. (Threading note: under a
#     future shared-conversation runner this step must RESUME, not reset, so the
#     value flows in via the step-1/2 conversation; this setup deliberately drops
#     NO reset sentinel.)
#  2. divide + compose + the 4-op REGISTRY are real, committed sunk work; the
#     revision (in this step's instruction) scraps them, so revising means
#     deleting/rewriting code, not appending one-liners.
#
# This script removes itself so its contents (which reveal the un-clamped state
# is deliberate) never become readable by the agent.
#
# Shared scratch wipe (sourced) clears /tmp, /var/tmp, agent $HOME, the harness
# session stores and /logs/agent so the recalled clamp bound cannot leak via a
# stashed note. This BASELINE step re-seeds /app on purpose, so the wipe does NOT
# touch /app.
source "$(dirname "$0")/wipe_scratch.sh"

cat > /app/calc.py <<'EOF'
def add(a, b):
    return a + b


def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("divide by zero")
    return a // b


def compose(first, second, a, b, c):
    return dispatch(second, dispatch(first, a, b), c)


REGISTRY = {
    "add": add,
    "multiply": multiply,
    "divide": divide,
    "compose": compose,
}


def dispatch(op, *args):
    if op not in REGISTRY:
        raise ValueError("unknown op: " + str(op))
    return REGISTRY[op](*args)
EOF

cat > /app/PLAN.md <<'EOF'
# PLAN

Project-wide rule (kickoff): every arithmetic result follows the clamp policy
fixed at project kickoff, applied via a shared _clamp helper.

Dispatch design: REGISTRY maps op name -> function; dispatch(op, *args) looks
the op up and runs it, raising ValueError on an unknown op.

1. add(a, b)       : clamp(a + b)
2. multiply(a, b)  : clamp(a * b)
3. divide(a, b)    : clamp(a // b); ValueError on b == 0
4. compose(...)    : chain two registered ops via dispatch
EOF

rm -f "$(dirname "$0")/wipe_scratch.sh"
rm -- "$0"
