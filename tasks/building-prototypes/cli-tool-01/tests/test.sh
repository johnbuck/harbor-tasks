#!/bin/bash
# Verifier — runs after the agent exits. Writes /logs/verifier/reward.json.
set -e

mkdir -p /logs/verifier

# Build test fixtures.
printf 'line1\nline2\nline3\nline4\nline5\nline6\nline7\n' > /tmp/seven.txt
> /tmp/empty.txt

# Run the tool under test.
out7="$(python /app/linecount.py /tmp/seven.txt 2>/dev/null | tr -d '[:space:]')" || true
out0="$(python /app/linecount.py /tmp/empty.txt 2>/dev/null | tr -d '[:space:]')" || true

if [ "$out7" = "7" ] && [ "$out0" = "0" ]; then
    correctness=1
else
    correctness=0
fi

echo "out7=$out7 out0=$out0" > /logs/verifier/check.log

# instruction_following: did the agent create the file at all?
if [ -f /app/linecount.py ]; then
    instruction_following=1
else
    instruction_following=0
fi

cat > /logs/verifier/reward.json <<EOF
{
  "correctness": ${correctness},
  "instruction_following": ${instruction_following},
  "reward": ${correctness}
}
EOF
