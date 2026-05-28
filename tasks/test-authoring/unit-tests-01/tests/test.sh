#!/bin/bash
# Mixed verifier: mutation-kill check (objective) + LLM judge (coverage quality).
set -e
mkdir -p /logs/verifier
cd /app

# 1. Agent's tests must PASS against the correct implementation.
if python -m pytest tests/test_slugify.py -q >/logs/verifier/pass_correct.log 2>&1; then
    pass_correct=1
else
    pass_correct=0
fi

# 2. Agent's tests must FAIL when the implementation is swapped for the mutant.
cp /app/stringutils.py /tmp/orig_stringutils.py
cp /opt/canonical/mutant_stringutils.py /app/stringutils.py
if python -m pytest tests/test_slugify.py -q >/logs/verifier/mutant.log 2>&1; then
    mutant_caught=0
else
    mutant_caught=1
fi
cp /tmp/orig_stringutils.py /app/stringutils.py

# 3. Did the agent tamper with the implementation under test?
if diff -q /app/stringutils.py /opt/canonical/stringutils.py >/dev/null 2>&1; then
    impl_untouched=1
else
    impl_untouched=0
fi

if [ "$pass_correct" = 1 ] && [ "$mutant_caught" = 1 ] && [ "$impl_untouched" = 1 ]; then
    correctness=1
else
    correctness=0
fi

export CORRECTNESS=$correctness
export INSTR_FOLLOWING=$impl_untouched
python /tests/judge_quality.py
