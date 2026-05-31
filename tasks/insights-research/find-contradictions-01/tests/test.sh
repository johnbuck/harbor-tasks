#!/bin/bash
# Deterministic graded verifier for find-contradictions-01.
#
# The report (/app/report.md) is a 4-section operating review with EIGHT planted
# internal contradictions of varying subtlety, plus TWO deliberate "near-miss"
# distractors that are NOT contradictions (a current-vs-future loyalty figure and
# an explicitly-superseded Q4 forecast). A discriminating harness retrieves and
# synthesizes across all four sections and reports the genuine eight WITHOUT
# tripping on the distractors.
#
# Scoring (graded fraction, NOT binary):
#   found      = # of the 8 genuine contradictions correctly identified
#                (both conflicting sides referenced in /app/contradictions.md)
#   fp         = # of distractor near-misses wrongly flagged as contradictions
#   reward     = max(0, found - fp) / 8        (float 0..1)
#   correctness= 1 iff found==8 AND fp==0, else 0
#
# Each genuine contradiction is detected by requiring BOTH distinctive sides to
# appear in the agent's report (token-pair match, case-insensitive).

set -u
mkdir -p /logs/verifier
TARGET=/app/contradictions.md

if [ ! -f "$TARGET" ]; then
  echo '{"reward": 0.0, "correctness": 0, "found": 0, "fp": 0, "missing_report": 1}' > /logs/verifier/reward.json
  exit 0
fi

a="$(tr '[:upper:]' '[:lower:]' < "$TARGET" 2>/dev/null)"
if [ -z "${a// /}" ]; then
  echo '{"reward": 0.0, "correctness": 0, "found": 0, "fp": 0, "empty_report": 1}' > /logs/verifier/reward.json
  exit 0
fi

has() { echo "$a" | grep -qE "$1"; }
# both(A,B): 1 iff both regexes A and B appear somewhere in the report
both() { if has "$1" && has "$2"; then echo 1; else echo 0; fi; }

# --- 8 genuine contradictions: each needs BOTH conflicting sides referenced ---

# C1 revenue direction: grew 12% over Q2  vs  came in below Q2 / declined
c1=$(both 'grew 12%|12% over q2|grew.*12|12%.*grow' 'below q2|declin|fell.*below|came in below')

# C2 gross margin: 41.3% / +80 bps   vs   39.1% / -120 bps / contraction
c2=$(both '41\.3|expand.*80|80 basis' '39\.1|120 basis|contract')

# C3 dividend: declared maiden dividend   vs   did not declare any dividend
c3=$(both 'declared.*dividend|maiden dividend' 'no(t)? declare.*dividend|did not declare|no dividend')

# C4 cash position: $84M net cash   vs   $46M net debt
c4=$(both '84 ?m|\$84|net cash' '46 ?m|\$46|net debt')

# C5 headcount: 5,200 employees   vs   6,050 employees
c5=$(both '5,?200' '6,?050')

# C6 largest hub: Reno largest   vs   Columbus largest
c6=$(both 'reno' 'columbus')

# C7 CAC direction: CAC fell 6%   vs   CAC rose 6%
c7=$(both 'cac fell|fell 6%|cac.*fell|fell.*6%.*acquisition' 'cac rose|rose 6%|cac.*rose|rose.*6%')

# C8 CEO name: Dana Whitfield   vs   Marcus Whitfield
c8=$(both 'dana whitfield|dana' 'marcus whitfield|marcus')

found=$((c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8))

# --- 2 distractor near-misses: penalize if flagged as a CONTRADICTION ---
# A flag is counted as a false positive only when the agent both mentions the
# distractor pair AND frames it with contradiction language nearby.

contra_lang='contradict|inconsist|conflict|discrepan|mismatch|does not match|do not match'

# D1 loyalty: "4.7 million" current vs "6 million" FY2026 target — NOT a contradiction
d1=0
if has '4\.7 ?million|4,?700,?000' && has '6 ?million|6,?000,?000'; then
  if echo "$a" | grep -qE "(loyal|member|enroll).{0,200}($contra_lang)|($contra_lang).{0,200}(loyal|member|enroll)"; then
    d1=1
  fi
fi

# D2 Q4 forecast: $455-470M earlier deck vs $420-435M revised — explicitly superseded
d2=0
if has '455|470' && has '420|435'; then
  if echo "$a" | grep -qE "(q4|forecast|guid).{0,200}($contra_lang)|($contra_lang).{0,200}(q4|forecast|guid)"; then
    d2=1
  fi
fi

fp=$((d1 + d2))

read reward correctness < <(python3 -c "
found=$found; fp=$fp; total=8
net=max(0, found - fp)
reward=round(net/total, 4)
corr=1 if (found==total and fp==0) else 0
print(reward, corr)
")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "found": ${found}, "total_genuine": 8, "fp": ${fp}, "c1": ${c1}, "c2": ${c2}, "c3": ${c3}, "c4": ${c4}, "c5": ${c5}, "c6": ${c6}, "c7": ${c7}, "c8": ${c8}, "d1_loyalty": ${d1}, "d2_forecast": ${d2}}
EOF
