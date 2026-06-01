#!/bin/bash
# Graded recall from memory: 18 markers + 3 needle facts = 21 checks (total).
# Difficulty levers:
#   - 18 random marker codes retained across 18 long-context turns.
#   - UPDATE-TRAP: the 3rd needle fact (RetentionYears) is stated as
#     "12" in chunk 1 then CORRECTED to "7" in chunk 14.
#     Credit is given ONLY for the latest value; the stale value earns nothing.
#   - DECOY penalty: two MARKER-D1/D2 codes in chunk 16 are labelled DRAFT;
#     listing either subtracts a point (clamped at 0).
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
echo "$a" | grep -q "8b17075d" && s=$((s+1))
echo "$a" | grep -q "2b55c626" && s=$((s+1))
echo "$a" | grep -q "03fd9a32" && s=$((s+1))
echo "$a" | grep -q "c34032b5" && s=$((s+1))
echo "$a" | grep -q "3b9db9d1" && s=$((s+1))
echo "$a" | grep -q "4d9ceef6" && s=$((s+1))
echo "$a" | grep -q "93cb2420" && s=$((s+1))
if echo "$a" | grep -q "8842"; then s=$((s+1)); fi
if echo "$a" | grep -q "meridian"; then s=$((s+1)); fi
if echo "$a" | grep -q "retentionyears: 7" || echo "$a" | grep -q "retention years: 7" || echo "$a" | grep -q "retentionyears:7"; then s=$((s+1)); fi
echo "$a" | grep -q "30e9d4da" && s=$((s-1))
echo "$a" | grep -q "413b3c9c" && s=$((s-1))
if [ "$s" -lt 0 ]; then s=0; fi
total=21
r=$(python3 -c "print(round(${s}/${total}, 4))")
if [ "$s" -eq "$total" ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"recalled\": ${s}}" > /logs/verifier/reward.json
