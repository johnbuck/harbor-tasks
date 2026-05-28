#!/bin/bash
# Deterministic recall check: project codename and deadline present (case-insensitive).
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
c=0
if echo "$a" | grep -q hyperion && (echo "$a" | grep -q "march 14" || echo "$a" | grep -q "march14"); then
    c=1
fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
