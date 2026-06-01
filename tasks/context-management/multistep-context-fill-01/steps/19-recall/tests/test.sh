#!/bin/bash
# Graded recall from memory: 18 markers + 3 needle facts = 21 checks (total).
# Difficulty levers:
#   - 18 random marker codes retained across 18 long-context turns.
#   - UPDATE-TRAP: the 3rd needle fact (LaunchWindow) is stated as
#     "2027-Q3" in chunk 1 then CORRECTED to "2027-Q4" in chunk 14.
#     Credit is given ONLY for the latest value; the stale value earns nothing.
#   - DECOY penalty: two MARKER-D1/D2 codes in chunk 16 are labelled DRAFT;
#     listing either subtracts a point (clamped at 0).
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
echo "$a" | grep -q "fdb6ba57" && s=$((s+1))
echo "$a" | grep -q "6a5479cd" && s=$((s+1))
echo "$a" | grep -q "ccffd399" && s=$((s+1))
echo "$a" | grep -q "9dc71ea9" && s=$((s+1))
echo "$a" | grep -q "8aa6f206" && s=$((s+1))
echo "$a" | grep -q "4231e66c" && s=$((s+1))
echo "$a" | grep -q "ae12be76" && s=$((s+1))
if echo "$a" | grep -q "helios"; then s=$((s+1)); fi
if echo "$a" | grep -q "vance"; then s=$((s+1)); fi
if echo "$a" | grep -q "2027-q4" || echo "$a" | grep -q "2027 q4"; then s=$((s+1)); fi
echo "$a" | grep -q "21ff7951" && s=$((s-1))
echo "$a" | grep -q "55e7694b" && s=$((s-1))
if [ "$s" -lt 0 ]; then s=0; fi
total=21
r=$(python3 -c "print(round(${s}/${total}, 4))")
if [ "$s" -eq "$total" ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"recalled\": ${s}}" > /logs/verifier/reward.json
