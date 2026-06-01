#!/bin/bash
# CONTEXT-ROT recall scorer for MERIDIAN HALL.
# 12 paraphrased questions; each answer is checked ON ITS OWN numbered line
# (line-anchored, so a verbose dump of all candidates on one line cannot score).
# Needles sit at controlled conversational depth -> the per-position subscores
# expose the rot CURVE:
#   EARLY  (Q1-4, visits 2-6)   = primacy edge
#   MIDDLE (Q5-8, visits 8-12)  = lost-in-the-middle (rot-critical)
#   LATE   (Q9-12, visits 14-18)= recency edge
# A harness that suffers rot shows MIDDLE << EARLY,LATE; one that actively manages
# context flattens it. Headline reward = correct / 12.
mkdir -p /logs/verifier
ans_line() { grep -iE "^[[:space:]]*$1[\.\)]" /app/answer.md 2>/dev/null | head -1; }
ok() { printf '%s' "$(ans_line "$1")" | grep -qiE "$2"; }

early=0; mid=0; late=0
ok 1  "pitch[ -]?pine"                        && early=$((early+1))
ok 2  "harcourt"                              && early=$((early+1))
ok 3  "1788"                                  && early=$((early+1))
ok 4  "nickel[ -]?bronze"                     && early=$((early+1))
ok 5  "aldhelm"                               && mid=$((mid+1))
ok 6  "crittall"                              && mid=$((mid+1))
ok 7  "white[ -]?oak"                         && mid=$((mid+1))
ok 8  "(14[,.]?000|fourteen[ -]thousand)"     && mid=$((mid+1))
ok 9  "pugin"                                 && late=$((late+1))
ok 10 "flemish"                               && late=$((late+1))
ok 11 "penrhyn"                               && late=$((late+1))
ok 12 "gillett"                               && late=$((late+1))

s=$((early+mid+late))
total=12
r=$(python3 -c "print(round(${s}/${total}, 4))")
if [ "$s" -eq "$total" ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"facts\": ${s}, \"early\": ${early}, \"middle\": ${mid}, \"late\": ${late}}" > /logs/verifier/reward.json
