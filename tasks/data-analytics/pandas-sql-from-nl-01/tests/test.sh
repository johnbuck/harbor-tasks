#!/bin/bash
# Verifier — runs after the agent exits. Writes /logs/verifier/reward.json.
set -e

mkdir -p /logs/verifier

expected="160.00"
got="$(tr -d '[:space:]' < /app/answer.txt 2>/dev/null || true)"

if [ "$got" = "$expected" ]; then
    correctness=1
else
    correctness=0
fi
echo "expected=$expected got=$got" > /logs/verifier/check.log

if diff -q /app/sales.csv /opt/canonical/sales.csv >/dev/null 2>&1; then
    data_untouched=1
else
    data_untouched=0
fi

cat > /logs/verifier/reward.json <<EOF
{
  "correctness": ${correctness},
  "instruction_following": ${data_untouched},
  "reward": ${correctness}
}
EOF
