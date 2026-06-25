#!/bin/bash
mkdir -p /logs/verifier
if [ -s /app/d5.txt ] && grep -qiE "pwd|cd|dirs" /app/d5.txt 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json
