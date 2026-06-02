#!/bin/bash
# Graded recall under PRECISION pressure: 12 of MY facts. reward = fraction.
# Four distractor turns planted confusable facts about OTHER people (Sam's
# shellfish/Mochi, Jess's Honda/Dune, Pat's Mar-4/Portland, a marine
# GEOlogist/crimson). A point is earned only when the answer states MY value AND
# does NOT also contain the sibling value — so an agent that confuses the two,
# OR hedges by dumping both, loses that point (fixes the prior false-1.0 where
# right+sibling co-present still scored). reward.json is a FLAT scalar dict.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
has() { printf '%s' "$a" | grep -Eq "$1"; }
no()  { ! printf '%s' "$a" | grep -Eq "$1"; }
s=0
# 1 cats: Pixel & Byte, NOT the coworker's cat Mochi
has 'pixel' && has 'byte' && no 'mochi' && s=$((s+1))
# 2 allergy: peanut, NOT shellfish
has 'peanut' && no 'shellfish' && s=$((s+1))
# 3 birthday: March 14, NOT March 4
has 'march 1?4|3/14|03/14|march fourteen' && no 'march 4\b|march fourth|3/4\b|03/04' && s=$((s+1))
# 4 profession: marine biologist, NOT geologist
has 'marine biologist' && no 'geologist' && s=$((s+1))
# 5 book: Left Hand of Darkness, NOT Dune
has 'left hand of darkness' && no '\bdune\b' && s=$((s+1))
# 6 hometown: Asheville, NOT Portland
has 'asheville' && no 'portland' && s=$((s+1))
# 7 car: make AND model AND (colour OR year), NOT the friend's Honda
has 'subaru' && has 'outback' && has 'blue|2019' && no '\bhonda\b' && s=$((s+1))
# 8 sister: Robin (no planted sibling)
has 'robin' && s=$((s+1))
# 9 favourite colour: teal, NOT crimson
has 'teal' && no 'crimson' && s=$((s+1))
# 10 coffee: cortado (no planted sibling)
has 'cortado' && s=$((s+1))
# 11 gym day: Tuesday (no planted sibling)
has 'tuesday' && s=$((s+1))
# 12 anniversary: June 2 (no planted sibling)
has 'june 2|6/2|june second' && s=$((s+1))

r=$(python3 -c "print(round(${s}/12, 4))")
if [ "$s" -eq 12 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts_recalled\": ${s}, \"facts_total\": 12}" > /logs/verifier/reward.json
