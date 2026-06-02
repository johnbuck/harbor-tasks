#!/bin/bash
# Graded recall under PRECISION pressure: 12 of MY facts. reward = fraction.
# Three distractor turns planted confusable facts about OTHER people (Tomas's
# lactose/terrier-Biscuit, Anjali's silver Mazda 3/Nov-12, Greg's Denver/
# Monday-yoga). A point is earned only when the answer states MY value AND does
# NOT also contain the sibling value — so confusing the two, or hedging by
# dumping both, loses that point (fixes the prior false-1.0). FLAT scalar dict.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
has() { printf '%s' "$a" | grep -Eq "$1"; }
no()  { ! printf '%s' "$a" | grep -Eq "$1"; }
s=0
# 1 dogs: Saffron & Pepper, NOT the colleague's terrier Biscuit
has 'saffron' && has 'pepper' && no 'biscuit' && s=$((s+1))
# 2 allergy: penicillin, NOT lactose
has 'penicillin' && no 'lactose' && s=$((s+1))
# 3 birthday: August 9, NOT November 12
has 'august 9|8/9|08/9|august ninth|august nine' && no 'november 12|11/12|november twelfth' && s=$((s+1))
# 4 profession: architect (no planted sibling)
has 'architect' && s=$((s+1))
# 5 book: Cloud Atlas (no planted sibling)
has 'cloud atlas' && s=$((s+1))
# 6 hometown: Madison, NOT Denver
has 'madison' && no 'denver' && s=$((s+1))
# 7 car: Mazda CX-5 green/2021, NOT the cousin's silver Mazda 3
has 'mazda' && has 'cx-5|cx5|cx 5' && has 'green|2021' && no 'silver|mazda 3\b|mazda3' && s=$((s+1))
# 8 brother: Devan (no planted sibling)
has 'devan' && s=$((s+1))
# 9 favourite colour: amber (no planted sibling)
has 'amber' && s=$((s+1))
# 10 coffee: cardamom latte (no planted sibling)
has 'cardamom' && s=$((s+1))
# 11 tennis day: Thursday, NOT Greg's Monday
has 'thursday' && no 'monday' && s=$((s+1))
# 12 anniversary: October 5 (no planted sibling)
has 'october 5|10/5|10/05|october fifth' && s=$((s+1))

r=$(python3 -c "print(round(${s}/12, 4))")
if [ "$s" -eq 12 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts_recalled\": ${s}, \"facts_total\": 12}" > /logs/verifier/reward.json
