#!/bin/bash
# Graded recall from memory: 11 markers + 3 needle facts = 14 checks.
# Retention of random marker codes across 11 long-context turns is where
# harness memory backends separate; graded fraction = the signal.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
s=0
echo "$a" | grep -q "ff82c4be" && s=$((s+1))
echo "$a" | grep -q "fc02dce8" && s=$((s+1))
echo "$a" | grep -q "423c1bd0" && s=$((s+1))
echo "$a" | grep -q "537a41d3" && s=$((s+1))
echo "$a" | grep -q "0478efaa" && s=$((s+1))
echo "$a" | grep -q "323f111f" && s=$((s+1))
echo "$a" | grep -q "b940a57c" && s=$((s+1))
echo "$a" | grep -q "6f4a1c6d" && s=$((s+1))
echo "$a" | grep -q "da31711d" && s=$((s+1))
echo "$a" | grep -q "c1944814" && s=$((s+1))
echo "$a" | grep -q "2116526c" && s=$((s+1))
if echo "$a" | grep -q "8842"; then s=$((s+1)); fi
if echo "$a" | grep -q "meridian"; then s=$((s+1)); fi
if echo "$a" | grep -q "retention"; then s=$((s+1)); fi
r=$(python3 -c "print(round(${s}/14, 4))")
if [ "$s" -eq 14 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"recalled\": ${s}}" > /logs/verifier/reward.json
