#!/bin/bash
# Graded recall under precision pressure: 12 of MY facts, reward = fraction
# correct. Four distractor turns planted other people's confusable facts
# (Sam's shellfish/Mochi, Jess's Honda/Dune, Pat's Mar-4/Portland, a marine
# GEOlogist/crimson) — a harness with weak memory precision writes the wrong
# value and earns no point for that field. Detail facts (the car) require all
# parts. Partial credit is the discrimination signal.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
s=0
# 1 cats: both names, NOT the coworker's cat Mochi
echo "$a" | grep -q pixel && echo "$a" | grep -q byte && s=$((s+1))
# 2 allergy: peanut, NOT shellfish
echo "$a" | grep -q peanut && s=$((s+1))
# 3 birthday: March 14, NOT March 4
echo "$a" | grep -Eq 'march 1?4|3/14|03/14|march fourteen' && s=$((s+1))
# 4 profession: marine biologist, NOT geologist
echo "$a" | grep -q 'marine biologist' && s=$((s+1))
# 5 book: Left Hand of Darkness, NOT Dune
echo "$a" | grep -q 'left hand of darkness' && s=$((s+1))
# 6 hometown: Asheville, NOT Portland
echo "$a" | grep -q asheville && s=$((s+1))
# 7 car: needs make AND model AND (colour OR year) — detail recall
echo "$a" | grep -q subaru && echo "$a" | grep -q outback \
    && { echo "$a" | grep -Eq 'blue|2019'; } && s=$((s+1))
# 8 sister
echo "$a" | grep -q robin && s=$((s+1))
# 9 favourite colour: teal, NOT crimson
echo "$a" | grep -q teal && s=$((s+1))
# 10 coffee: cortado
echo "$a" | grep -q cortado && s=$((s+1))
# 11 gym day: Tuesday
echo "$a" | grep -q tuesday && s=$((s+1))
# 12 anniversary: June 2
echo "$a" | grep -Eq 'june 2|6/2|june second' && s=$((s+1))

r=$(python3 -c "print(round(${s}/12, 4))")
if [ "$s" -eq 12 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts_recalled\": ${s}, \"facts_total\": 12}" > /logs/verifier/reward.json
