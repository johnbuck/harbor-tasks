#!/bin/bash
# Graded recall from memory: 18 markers + 3 needle facts = 21 checks (total).
# Difficulty levers:
#   - 18 random marker codes retained across 18 long-context turns.
#   - UPDATE-TRAP: the 3rd needle fact (CoolantType) is stated as
#     "R-410A" in chunk 1 then CORRECTED to "R-32" in chunk 14.
#     Credit is given ONLY for the latest value; the stale value earns nothing.
#   - DECOY penalty: two MARKER-D1/D2 codes in chunk 16 are labelled DRAFT;
#     listing either subtracts a point (clamped at 0).
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
echo "$a" | grep -q "0f41a399" && s=$((s+1))
echo "$a" | grep -q "1eaf1aef" && s=$((s+1))
echo "$a" | grep -q "bb7fbc81" && s=$((s+1))
echo "$a" | grep -q "6d57718d" && s=$((s+1))
echo "$a" | grep -q "80b94692" && s=$((s+1))
echo "$a" | grep -q "520c0391" && s=$((s+1))
echo "$a" | grep -q "b459e236" && s=$((s+1))
if echo "$a" | grep -q "b12"; then s=$((s+1)); fi
if echo "$a" | grep -q "vault 7" || echo "$a" | grep -q "vault7"; then s=$((s+1)); fi
if echo "$a" | grep -q "r-32" || echo "$a" | grep -q "r32"; then s=$((s+1)); fi
echo "$a" | grep -q "84ad8527" && s=$((s-1))
echo "$a" | grep -q "79125e05" && s=$((s-1))
if [ "$s" -lt 0 ]; then s=0; fi
total=21
r=$(python3 -c "print(round(${s}/${total}, 4))")
if [ "$s" -eq "$total" ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"recalled\": ${s}}" > /logs/verifier/reward.json
