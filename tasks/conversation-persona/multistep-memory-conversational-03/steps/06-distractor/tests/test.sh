#!/bin/bash
mkdir -p /logs/verifier
got="$(tr -d "[:space:]" < /app/d6.txt 2>/dev/null | tr "[:upper:]" "[:lower:]")"
if [ "$got" = "yromem" ]; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
