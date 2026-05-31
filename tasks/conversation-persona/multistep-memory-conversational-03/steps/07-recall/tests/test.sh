#!/bin/bash
# Graded recall: 6 facts, reward = fraction correct (retrieval reliability under
# load is the harness discriminator; binary would collapse to BLUNT).
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
s=0
echo "$a" | grep -q comet && s=$((s+1))                                       # dog name
echo "$a" | grep -q shellfish && s=$((s+1))                                   # allergy
echo "$a" | grep -Eq 'june 22|june 22nd|6/22|06/22|june twenty' && s=$((s+1))  # anniversary
echo "$a" | grep -q 'structural engineer' && s=$((s+1))                        # profession
echo "$a" | grep -q 'blade runner 2049' && s=$((s+1))                          # film
echo "$a" | grep -q boise && s=$((s+1))                                        # hometown
r=$(python3 -c "print(round(${s}/6, 4))")
if [ "$s" -eq 6 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts_recalled\": ${s}}" > /logs/verifier/reward.json
