#!/bin/bash
# Deterministic graded mutation-coverage verifier for unit-tests-01 (medium).
#
# The agent writes /app/tests/test_slugify.py for slugify(). We grade by
# MUTATION: the suite must pass against the correct implementation, leave the
# implementation untouched, and then KILL each of four independent mutants —
# one per target behavior:
#   M1  lowercasing
#   M2  collapsing runs of separators to a SINGLE hyphen
#   M3  stripping leading/trailing hyphens
#   M4  preserving digits/alphanumerics
#
# A test suite that passes the correct impl but fails to catch a mutant earns
# no point for that behavior. Score = fraction of mutants killed.
#
#   pass_correct  : 1 if suite passes on the real impl (gate)
#   impl_untouched: 1 if /app/stringutils.py is unmodified (gate)
#   killed        : number of the 4 mutants the suite catches (only counted when
#                   both gates pass; a suite that doesn't pass the real impl, or
#                   that tampers with the impl, scores 0)
#   reward        = round(killed / 4, 4)   (0 if either gate fails)
#   correctness   = 1 iff pass_correct AND impl_untouched AND killed == 4
#
# reward.json MUST stay a FLAT dict of scalar numbers (FOOTGUNS #38).
set -u
mkdir -p /logs/verifier
cd /app

TEST=tests/test_slugify.py
if [ ! -f "$TEST" ]; then
    cat > /logs/verifier/reward.json <<EOF
{"reward": 0, "correctness": 0, "instruction_following": 0, "pass_correct": 0, "impl_untouched": 0, "killed": 0, "total_mutants": 4, "m1": 0, "m2": 0, "m3": 0, "m4": 0}
EOF
    exit 0
fi
instruction_following=1

# Gate 1: tests pass against the correct implementation.
if python -m pytest "$TEST" -q >/logs/verifier/pass_correct.log 2>&1; then
    pass_correct=1
else
    pass_correct=0
fi

# Gate 2: implementation under test is unmodified.
if diff -q /app/stringutils.py /opt/canonical/stringutils.py >/dev/null 2>&1; then
    impl_untouched=1
else
    impl_untouched=0
fi

# Mutation: swap in each mutant, run the suite; a non-zero exit = mutant killed.
cp /app/stringutils.py /tmp/orig_stringutils.py
declare -A KILL
for m in m1 m2 m3 m4; do
    case "$m" in
        m1) src=/tests/mutants/m1_no_lowercase.py ;;
        m2) src=/tests/mutants/m2_no_collapse.py ;;
        m3) src=/tests/mutants/m3_no_strip_hyphens.py ;;
        m4) src=/tests/mutants/m4_strips_digits.py ;;
    esac
    cp "$src" /app/stringutils.py
    if python -m pytest "$TEST" -q >"/logs/verifier/mutant_${m}.log" 2>&1; then
        KILL[$m]=0   # suite passed on the mutant -> NOT caught
    else
        KILL[$m]=1   # suite failed on the mutant -> caught
    fi
done
cp /tmp/orig_stringutils.py /app/stringutils.py

m1=${KILL[m1]}; m2=${KILL[m2]}; m3=${KILL[m3]}; m4=${KILL[m4]}

read reward correctness killed < <(python3 -c "
pc=$pass_correct; iu=$impl_untouched
kills = $m1 + $m2 + $m3 + $m4
if pc==1 and iu==1:
    killed = kills
else:
    killed = 0
reward = round(killed/4, 4)
corr = 1 if (pc==1 and iu==1 and killed==4) else 0
print(reward, corr, killed)
")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "instruction_following": ${instruction_following}, "pass_correct": ${pass_correct}, "impl_untouched": ${impl_untouched}, "killed": ${killed}, "total_mutants": 4, "m1_lowercase": ${m1}, "m2_collapse": ${m2}, "m3_strip_hyphens": ${m3}, "m4_digits": ${m4}}
EOF
