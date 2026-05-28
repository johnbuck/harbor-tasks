#!/bin/bash
# Recall step: answer.md must contain both the rate limit and the auth header name.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
c=0
if echo "$a" | grep -q "100" && echo "$a" | grep -q "x-acme-key"; then
    c=1
fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
