#!/bin/bash
mkdir -p /logs/verifier
got="$(tr -d '[:space:]' < /app/scratch.txt 2>/dev/null)"
if [ "$got" = "123" ]; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
