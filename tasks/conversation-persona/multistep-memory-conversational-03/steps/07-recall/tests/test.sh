#!/bin/bash
# Graded recall under precision pressure: 12 of MY facts, reward = fraction
# correct. Four distractor turns planted other people's confusable facts
# (Hassan's bee-sting/beagle-Waffles, Dario's black Corolla & Arrival,
# Priscilla's Reno & Sunday-runs, Owen's maroon & 3rd-floor) — a harness with
# weak memory precision writes the wrong value and earns no point for that
# field. Detail facts (the car) require all parts. Partial credit is the
# discrimination signal.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
s=0
# 1 dog: Comet, NOT the brother-in-law's beagle Waffles
echo "$a" | grep -q comet && s=$((s+1))
# 2 allergy: shellfish, NOT bee stings
echo "$a" | grep -q shellfish && s=$((s+1))
# 3 anniversary: June 22
echo "$a" | grep -Eq 'june 22|june 22nd|6/22|06/22|june twenty' && s=$((s+1))
# 4 profession: structural engineer
echo "$a" | grep -q 'structural engineer' && s=$((s+1))
# 5 film: Blade Runner 2049, NOT Arrival
echo "$a" | grep -q 'blade runner 2049' && s=$((s+1))
# 6 hometown: Boise, NOT Reno
echo "$a" | grep -q boise && s=$((s+1))
# 7 car: needs make AND model AND (colour OR year) — detail recall.
#   Requires Tacoma (NOT the friend's "Corolla"); model token disambiguates.
echo "$a" | grep -q toyota && echo "$a" | grep -q tacoma \
    && { echo "$a" | grep -Eq 'red|2018'; } && s=$((s+1))
# 8 daughters: both twin names
echo "$a" | grep -q lena && echo "$a" | grep -q mira && s=$((s+1))
# 9 favorite color: olive, NOT maroon
echo "$a" | grep -q olive && s=$((s+1))
# 10 floor: 12th, NOT 3rd
echo "$a" | grep -Eq '12th floor|floor 12|12th|twelfth' && s=$((s+1))
# 11 coffee: double espresso
echo "$a" | grep -q 'double espresso' && s=$((s+1))
# 12 run day: Saturday, NOT Sunday
echo "$a" | grep -q saturday && s=$((s+1))

r=$(python3 -c "print(round(${s}/12, 4))")
if [ "$s" -eq 12 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts_recalled\": ${s}, \"facts_total\": 12}" > /logs/verifier/reward.json
