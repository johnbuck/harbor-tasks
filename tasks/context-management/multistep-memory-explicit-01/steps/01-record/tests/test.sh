#!/bin/bash
# Record step: verify that all key facts were persisted somewhere under /app
# (excluding answer.md and scratch.txt which belong to other steps).
mkdir -p /logs/verifier

found_acme=0
found_rate=0
found_header=0

while IFS= read -r -d '' f; do
    content="$(tr '[:upper:]' '[:lower:]' < "$f" 2>/dev/null)"
    echo "$content" | grep -q "acme.io"  && found_acme=1
    echo "$content" | grep -q "100"      && found_rate=1
    echo "$content" | grep -q "x-acme-key" && found_header=1
done < <(find /app -type f ! -name "answer.md" ! -name "scratch.txt" -print0 2>/dev/null)

if [ "$found_acme" = "1" ] && [ "$found_rate" = "1" ] && [ "$found_header" = "1" ]; then
    c=1
else
    c=0
fi

echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
