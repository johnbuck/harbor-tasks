#!/bin/bash
# 3600 / 45 = 80
mkdir -p /logs/verifier
if grep -q 80 /app/refresh.txt 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
