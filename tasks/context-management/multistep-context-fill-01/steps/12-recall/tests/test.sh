#!/bin/bash
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
if echo "$a" | grep -q "helios" && echo "$a" | grep -q "2027-q3"; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
