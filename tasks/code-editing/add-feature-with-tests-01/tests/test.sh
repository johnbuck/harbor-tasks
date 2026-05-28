#!/bin/bash
set -e

mkdir -p /logs/verifier
cd /app

if python -m pytest tests/test_lru.py -v >/logs/verifier/pytest.log 2>&1; then
    correctness=1
else
    correctness=0
fi

if diff -q /app/tests/test_lru.py /opt/canonical/test_lru.py >/dev/null 2>&1; then
    test_untouched=1
else
    test_untouched=0
fi

cat > /logs/verifier/reward.json <<EOF
{
  "correctness": ${correctness},
  "instruction_following": ${test_untouched},
  "reward": ${correctness}
}
EOF
