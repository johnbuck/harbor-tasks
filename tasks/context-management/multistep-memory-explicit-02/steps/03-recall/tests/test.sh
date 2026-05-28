#!/bin/bash
# Recall step: answer.md must contain both the schema name and the backup time.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
c=0
if echo "$a" | grep -q "billing" && echo "$a" | grep -q "02:00"; then
    c=1
fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
