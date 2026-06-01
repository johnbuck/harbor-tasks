#!/bin/bash
# Graded recall under precision pressure: 12 of MY facts, reward = fraction
# correct. Three distractor turns planted other people's confusable facts
# (Tomas's lactose/terrier-Biscuit, Anjali's silver Mazda 3 & Nov-12, Greg's
# Denver & Monday-yoga) — a harness with weak memory precision writes the wrong
# value and earns no point for that field. Detail facts (the car) require all
# parts. Partial credit is the discrimination signal.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
s=0
# 1 dogs: both names, NOT the colleague's terrier Biscuit
echo "$a" | grep -q saffron && echo "$a" | grep -q pepper && s=$((s+1))
# 2 allergy: penicillin, NOT lactose
echo "$a" | grep -q penicillin && s=$((s+1))
# 3 birthday: August 9, NOT November 12
echo "$a" | grep -Eq 'august 9|8/9|08/9|august ninth|august nine' && s=$((s+1))
# 4 profession: architect
echo "$a" | grep -q architect && s=$((s+1))
# 5 book: Cloud Atlas
echo "$a" | grep -q 'cloud atlas' && s=$((s+1))
# 6 hometown: Madison, NOT Denver
echo "$a" | grep -q madison && s=$((s+1))
# 7 car: needs make AND model AND (colour OR year) — detail recall.
#   Requires CX-5 (NOT the cousin's plain "Mazda 3"); model token disambiguates.
echo "$a" | grep -q mazda && echo "$a" | grep -Eq 'cx-5|cx5|cx 5' \
    && { echo "$a" | grep -Eq 'green|2021'; } && s=$((s+1))
# 8 brother
echo "$a" | grep -q devan && s=$((s+1))
# 9 favourite colour: amber
echo "$a" | grep -q amber && s=$((s+1))
# 10 coffee: cardamom latte
echo "$a" | grep -q cardamom && s=$((s+1))
# 11 tennis day: Thursday, NOT Monday
echo "$a" | grep -q thursday && s=$((s+1))
# 12 anniversary: October 5
echo "$a" | grep -Eq 'october 5|10/5|10/05|october fifth' && s=$((s+1))

r=$(python3 -c "print(round(${s}/12, 4))")
if [ "$s" -eq 12 ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts_recalled\": ${s}, \"facts_total\": 12}" > /logs/verifier/reward.json
