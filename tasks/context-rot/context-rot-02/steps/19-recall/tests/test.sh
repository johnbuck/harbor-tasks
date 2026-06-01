#!/bin/bash
# CONTEXT-ROT MULTI-HOP scorer for WESTMARCH PRIORY.
# 8 two-hop chains; each final answer checked ON ITS OWN numbered line
# (line-anchored). Chains bucketed by depth -> the subscores expose the rot curve:
#   EARLY  (Q1-2, both hops visits 2-6)   = primacy-protected
#   MIDDLE (Q3-5, both hops visits 8-12)  = lost-in-the-middle, rot-critical
#   LATE   (Q6-8, both hops visits 14-18) = recency-protected
# Rot breaks a chain if EITHER hop is lost, so MIDDLE << EARLY,LATE signals rot;
# a harness with active context management flattens it. Reward = correct / 8.
mkdir -p /logs/verifier
ans_line() { grep -iE "^[[:space:]]*$1[\.\)]" /app/answer.md 2>/dev/null | head -1; }
ok() { printf '%s' "$(ans_line "$1")" | grep -qiE "$2"; }

early=0; mid=0; late=0
ok 1 "lyon"                        && early=$((early+1))
ok 2 "jackfield"                   && early=$((early+1))
ok 3 "thames"                      && mid=$((mid+1))
ok 4 "(saint|st\.?)[ -]?luke"      && mid=$((mid+1))
ok 5 "durham"                      && mid=$((mid+1))
ok 6 "hereford"                    && late=$((late+1))
ok 7 "loughborough"                && late=$((late+1))
ok 8 "latvia"                      && late=$((late+1))

s=$((early+mid+late)); total=8
r=$(python3 -c "print(round(${s}/${total}, 4))")
if [ "$s" -eq "$total" ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"chains\": ${s}, \"early\": ${early}, \"middle\": ${mid}, \"late\": ${late}}" > /logs/verifier/reward.json
