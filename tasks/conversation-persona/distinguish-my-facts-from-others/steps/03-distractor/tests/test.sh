#!/bin/bash
mkdir -p /logs/verifier
got="$(tr -d "[:space:]" < /app/d3.txt 2>/dev/null)"
if [ "$got" = "1123581321" ]; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
