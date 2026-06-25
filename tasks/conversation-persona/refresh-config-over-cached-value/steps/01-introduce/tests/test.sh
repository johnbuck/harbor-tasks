#!/bin/bash
mkdir -p /logs/verifier
if grep -q 45 /app/seen.txt 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
