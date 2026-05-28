#!/bin/bash
# Record step: verify that all key facts were persisted somewhere under /app
# (excluding answer.md and scratch.txt which belong to other steps).
mkdir -p /logs/verifier

found_postgres=0
found_billing=0
found_time=0

while IFS= read -r -d '' f; do
    content="$(tr '[:upper:]' '[:lower:]' < "$f" 2>/dev/null)"
    echo "$content" | grep -q "postgres"  && found_postgres=1
    echo "$content" | grep -q "billing"   && found_billing=1
    echo "$content" | grep -q "02:00"     && found_time=1
done < <(find /app -type f ! -name "answer.md" ! -name "scratch.txt" -print0 2>/dev/null)

if [ "$found_postgres" = "1" ] && [ "$found_billing" = "1" ] && [ "$found_time" = "1" ]; then
    c=1
else
    c=0
fi

echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
