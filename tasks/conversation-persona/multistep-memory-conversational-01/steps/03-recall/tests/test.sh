#!/bin/bash
# Deterministic recall check: all three facts present (case-insensitive).
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
c=0
if echo "$a" | grep -q pixel && echo "$a" | grep -q byte && echo "$a" | grep -q peanut; then
    c=1
fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
