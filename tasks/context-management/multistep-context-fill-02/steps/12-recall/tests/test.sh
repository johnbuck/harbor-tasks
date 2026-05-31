#!/bin/bash
# Graded recall from memory: 11 markers + 3 needle facts = 14 checks.
# Retention of random marker codes across 11 long-context turns is where
# harness memory backends separate; graded fraction = the signal.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
s=0
echo "$a" | grep -q "65f34746" && s=$((s+1))
echo "$a" | grep -q "9d6fc5c7" && s=$((s+1))
echo "$a" | grep -q "c1d448ca" && s=$((s+1))
echo "$a" | grep -q "28231e80" && s=$((s+1))
echo "$a" | grep -q "25b1b5db" && s=$((s+1))
echo "$a" | grep -q "4ab38c09" && s=$((s+1))
echo "$a" | grep -q "7fd4d03e" && s=$((s+1))
echo "$a" | grep -q "654693c8" && s=$((s+1))
echo "$a" | grep -q "43dd1f4c" && s=$((s+1))
echo "$a" | grep -q "fe1a88fd" && s=$((s+1))
echo "$a" | grep -q "3ba114f7" && s=$((s+1))
if echo "$a" | grep -q "b12"; then s=$((s+1)); fi
if echo "$a" | grep -q "vault 7" || echo "$a" | grep -q "vault7"; then s=$((s+1)); fi
if echo "$a" | grep -q "r-410a" || echo "$a" | grep -q "r410a"; then s=$((s+1)); fi
r=$(python3 -c "print(round(${s}/14, 4))")
if [ "$s" -eq 14 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"recalled\": ${s}}" > /logs/verifier/reward.json
