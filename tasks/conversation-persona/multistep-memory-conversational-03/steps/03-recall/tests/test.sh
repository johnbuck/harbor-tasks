#!/bin/bash
# Deterministic recall check: car make and gym street present (case-insensitive).
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
c=0
if echo "$a" | grep -q subaru && echo "$a" | grep -q oak; then
    c=1
fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
