#!/bin/bash
# Graded recall from memory: 11 markers + 3 needle facts = 14 checks.
# Retention of random marker codes across 11 long-context turns is where
# harness memory backends separate; graded fraction = the signal.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
s=0
echo "$a" | grep -q "25ec9096" && s=$((s+1))
echo "$a" | grep -q "48ba5864" && s=$((s+1))
echo "$a" | grep -q "7961c596" && s=$((s+1))
echo "$a" | grep -q "57d53498" && s=$((s+1))
echo "$a" | grep -q "5fff0226" && s=$((s+1))
echo "$a" | grep -q "8c86ba15" && s=$((s+1))
echo "$a" | grep -q "60cb5028" && s=$((s+1))
echo "$a" | grep -q "fa38b5b7" && s=$((s+1))
echo "$a" | grep -q "9da83e08" && s=$((s+1))
echo "$a" | grep -q "896aef63" && s=$((s+1))
echo "$a" | grep -q "7f4af9f8" && s=$((s+1))
if echo "$a" | grep -q "helios"; then s=$((s+1)); fi
if echo "$a" | grep -q "vance"; then s=$((s+1)); fi
if echo "$a" | grep -q "2027-q3" || echo "$a" | grep -q "2027 q3"; then s=$((s+1)); fi
r=$(python3 -c "print(round(${s}/14, 4))")
if [ "$s" -eq 14 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"recalled\": ${s}}" > /logs/verifier/reward.json
