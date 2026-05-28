#!/bin/bash
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
if echo "$a" | grep -q "b12" && echo "$a" | grep -q "r-410a"; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
