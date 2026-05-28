#!/bin/bash
# Verifier — runs after the agent exits. Writes /logs/verifier/reward.json.
set -e

mkdir -p /logs/verifier

# instruction_following: findings.txt must exist.
if [ -f /app/findings.txt ]; then
    instruction_following=1
else
    instruction_following=0
    cat > /logs/verifier/reward.json <<EOF
{
  "correctness": 0,
  "instruction_following": 0,
  "reward": 0
}
EOF
    exit 0
fi

# Normalize the agent's output:
#   - strip leading/trailing whitespace per line
#   - drop empty lines
#   - strip a leading "repo/" or "./" prefix if present
#   - sort and dedupe
normalized="$(sed 's/^[[:space:]]*//;s/[[:space:]]*$//' /app/findings.txt \
    | grep -v '^$' \
    | sed 's|^repo/||;s|^\./||' \
    | sort -u)"

expected="$(printf 'auth.py\nconfig.py')"

if [ "$normalized" = "$expected" ]; then
    correctness=1
else
    correctness=0
fi

printf 'normalized:\n%s\nexpected:\n%s\n' "$normalized" "$expected" \
    > /logs/verifier/check.log

cat > /logs/verifier/reward.json <<EOF
{
  "correctness": ${correctness},
  "instruction_following": ${instruction_following},
  "reward": ${correctness}
}
EOF
