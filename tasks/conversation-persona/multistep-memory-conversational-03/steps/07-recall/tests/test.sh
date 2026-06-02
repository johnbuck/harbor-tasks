#!/bin/bash
# Graded recall under PRECISION pressure: 12 of MY facts. reward = fraction.
# Four distractor turns planted confusable facts about OTHER people (Hassan's
# bee-sting/beagle-Waffles, Dario's black Corolla/Arrival, Priscilla's Reno/
# Sunday, Owen's maroon/3rd-floor). A point is earned only when the answer
# states MY value AND does NOT also contain the sibling value — so confusing the
# two, or hedging by dumping both, loses that point. FLAT scalar dict.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
has() { printf '%s' "$a" | grep -Eq "$1"; }
no()  { ! printf '%s' "$a" | grep -Eq "$1"; }
s=0
# 1 dog: Comet, NOT the brother-in-law's beagle Waffles
has 'comet' && no 'waffles' && s=$((s+1))
# 2 allergy: shellfish, NOT bee stings
has 'shellfish' && no 'bee sting' && s=$((s+1))
# 3 anniversary: June 22 (no planted sibling)
has 'june 22|june 22nd|6/22|06/22|june twenty' && s=$((s+1))
# 4 profession: structural engineer (no planted sibling)
has 'structural engineer' && s=$((s+1))
# 5 film: Blade Runner 2049, NOT Arrival
has 'blade runner 2049' && no '\barrival\b' && s=$((s+1))
# 6 hometown: Boise, NOT Reno
has 'boise' && no 'reno' && s=$((s+1))
# 7 car: Toyota Tacoma red/2018, NOT the friend's black Corolla
has 'toyota' && has 'tacoma' && has 'red|2018' && no 'corolla|black' && s=$((s+1))
# 8 daughters: twins Lena & Mira (no planted sibling)
has 'lena' && has 'mira' && s=$((s+1))
# 9 favorite color: olive, NOT maroon
has 'olive' && no 'maroon' && s=$((s+1))
# 10 floor: 12th, NOT the manager's 3rd
has '12th floor|floor 12|12th|twelfth' && no '3rd floor|floor 3\b|third floor' && s=$((s+1))
# 11 coffee: double espresso (no planted sibling)
has 'double espresso' && s=$((s+1))
# 12 run day: Saturday, NOT Priscilla's Sunday
has 'saturday' && no 'sunday' && s=$((s+1))

r=$(python3 -c "print(round(${s}/12, 4))")
if [ "$s" -eq 12 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts_recalled\": ${s}, \"facts_total\": 12}" > /logs/verifier/reward.json
