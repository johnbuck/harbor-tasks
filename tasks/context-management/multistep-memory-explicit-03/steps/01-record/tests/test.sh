#!/bin/bash
# Record step: verify that all key facts were persisted somewhere under /app
# (excluding answer.md and scratch.txt which belong to other steps).
mkdir -p /logs/verifier

found_tag=0
found_rollback=0
found_oncall=0

while IFS= read -r -d '' f; do
    content="$(tr '[:upper:]' '[:lower:]' < "$f" 2>/dev/null)"
    echo "$content" | grep -q "v3.2.1"        && found_tag=1
    echo "$content" | grep -q "make rollback"  && found_rollback=1
    echo "$content" | grep -q "jordan"         && found_oncall=1
done < <(find /app -type f ! -name "answer.md" ! -name "scratch.txt" -print0 2>/dev/null)

if [ "$found_tag" = "1" ] && [ "$found_rollback" = "1" ] && [ "$found_oncall" = "1" ]; then
    c=1
else
    c=0
fi

echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
