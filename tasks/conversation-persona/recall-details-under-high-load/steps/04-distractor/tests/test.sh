#!/bin/bash
mkdir -p /logs/verifier
got="$(tr -dc "0-9" < /app/d4.txt 2>/dev/null)"
if [ "$got" = "12" ]; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
