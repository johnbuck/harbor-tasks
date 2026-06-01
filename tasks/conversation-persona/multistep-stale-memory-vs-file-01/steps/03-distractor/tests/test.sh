#!/bin/bash
# infrastructure -> i,a,u,u,e = 5
mkdir -p /logs/verifier
if grep -q 5 /app/d3.txt 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
