#!/bin/bash
# Verifier reads /app/answer.md and scores three dimensions:
#   - vegetarian (no meat/fish mentioned)
#   - peanut-free (no peanut mention, or explicit avoidance)
#   - timing-acknowledged (5 PM PT is climbing-night-adjacent; Tuesday = climbing night;
#     bonus if the answer notes light/portable for energy or fits-around-climbing)
#
# Multi-axis reward emitted. The memory_inspection axis (whether the harness's
# recall group / hindsight bank actually has the facts persisted) is computed by
# the trial-level orchestrator post-run; per-step verifier can't reach wiley
# from inside the trial sandbox reliably.
set -u
mkdir -p /logs/verifier

if [ ! -s /app/answer.md ]; then
    cat > /logs/verifier/reward.json <<'EOF'
{"reward": 0.0, "correctness": 0.0, "vegetarian": 0, "peanut_free": 0, "timing_aware": 0, "no_reclarify": 0}
EOF
    exit 0
fi

ans=$(tr '[:upper:]' '[:lower:]' < /app/answer.md)

# Vegetarian check: no obvious meat words (case-insensitive).
meat_pat='chicken|beef|pork|bacon|sausage|fish|salmon|tuna|shrimp|prawn|lamb|turkey|duck|ham|steak|carnitas|pancetta|prosciutto'
veg=1
echo "$ans" | grep -qE "$meat_pat" && veg=0

# Peanut-free check: either no mention, or explicit avoidance language.
peanut=1
if echo "$ans" | grep -q 'peanut'; then
    # Tolerate "no peanut", "without peanut", "skip peanut", "avoid peanut",
    # "peanut-free", "peanut free", "no peanuts".
    if ! echo "$ans" | grep -qE '(no|without|skip|avoid|free of|free from) peanut|peanut[- ]free'; then
        peanut=0
    fi
fi

# Timing/Tuesday/climbing awareness — bonus, not strict.
timing=0
if echo "$ans" | grep -qE 'tuesday|climb|bouldering|pre-climb|post-climb|before climb|after climb|light|portable|easy to digest|energy'; then
    timing=1
fi

# No re-clarification: agent shouldn't ask the user to re-state facts.
noreclar=1
if echo "$ans" | grep -qE 'could you (remind|tell|share|let me know)|what (are|is) your|do you (have|eat|like)|are you (vegetarian|vegan|allergic)'; then
    noreclar=0
fi

# Reward: vegetarian + peanut_free are MUST (multiplicative);
# timing and no-reclarify are bonuses (additive +0.1 each, capped 1.0).
reward=$(python3 -c "
base = $veg * $peanut
bonus = 0.1 * $timing + 0.1 * $noreclar
print(min(1.0, base * 0.8 + bonus + base * 0.1))
" )

correctness=$(python3 -c "print($veg * $peanut)")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "vegetarian": ${veg}, "peanut_free": ${peanut}, "timing_aware": ${timing}, "no_reclarify": ${noreclar}}
EOF
