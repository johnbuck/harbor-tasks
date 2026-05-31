#!/bin/bash
# Graded recall: 6 facts, reward = fraction correct. Retrieval reliability
# under load is where harness memory backends separate, so partial credit is
# the discrimination signal (binary would collapse to BLUNT).
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
s=0
echo "$a" | grep -q pixel && echo "$a" | grep -q byte && s=$((s+1))        # cats
echo "$a" | grep -q peanut && s=$((s+1))                                    # allergy
echo "$a" | grep -Eq 'march 1?4|3/14|03/14|march fourteen' && s=$((s+1))    # birthday
echo "$a" | grep -q biologist && s=$((s+1))                                 # profession
echo "$a" | grep -q 'left hand of darkness' && s=$((s+1))                   # book
echo "$a" | grep -q asheville && s=$((s+1))                                 # hometown
r=$(python3 -c "print(round(${s}/6, 4))")
# correctness = 1 only if ALL six recalled (strict), reward = graded fraction
if [ "$s" -eq 6 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts_recalled\": ${s}}" > /logs/verifier/reward.json
