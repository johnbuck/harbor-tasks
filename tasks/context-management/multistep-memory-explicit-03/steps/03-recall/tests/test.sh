#!/bin/bash
# Recall step: answer.md must contain both the release tag and the on-call name.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
c=0
if echo "$a" | grep -q "v3.2.1" && echo "$a" | grep -q "jordan"; then
    c=1
fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
