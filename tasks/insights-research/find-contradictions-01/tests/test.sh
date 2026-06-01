#!/bin/bash
# Deterministic graded verifier for find-contradictions-01 (HARD).
#
# The report (/app/report.md) is a 4-section operating review with TWELVE planted
# internal contradictions of varying subtlety, plus FOUR deliberate "near-miss"
# distractors that are NOT contradictions:
#   D1 current loyalty 4.7M vs 6M FY2026 target   (current vs future)
#   D2 Q4 $455-470M deck vs $420-435M revised      (explicitly superseded)
#   D3 Home & Garden $120M vs $412M Q3 total        (subtotal vs total — a subset)
#   D4 FY2025 capex $58M vs FY2026 capex $70M       (different fiscal years)
# A discriminating harness retrieves and synthesizes across all sections and
# reports the genuine twelve WITHOUT tripping on the four distractors.
#
# Scoring (graded fraction = precision+recall over the contradiction set):
#   found      = # of the 12 genuine contradictions correctly identified
#                (both conflicting sides referenced in /app/contradictions.md)
#   fp         = # of distractor near-misses wrongly flagged as contradictions
#   reward     = max(0, found - fp) / 12        (float 0..1)
#   correctness= 1 iff found==12 AND fp==0, else 0

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
both() { if has "$1" && has "$2"; then echo 1; else echo 0; fi; }

# --- 12 genuine contradictions: each needs BOTH conflicting sides referenced ---

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
# C9 channel mix: online 55% majority   vs   in-store 58% majority
c9=$(both 'online.*55%|55% of total|55%.*online' 'in-store.*58%|58% of total|in-store.*majority|58%.*in-store')
# C10 store count: 412 stores   vs   388-store footprint (require store context)
c10=$(both '412 (retail )?stores?|412.*store|store.*412' '388[- ]?store|388 (retail )?stores?|store.*388')
# C11 NPS: climbed to 71   vs   slipped to 54
c11=$(both 'nps.*71|71.*nps|score.*71|climb.*71' 'nps.*54|54.*nps|slip.*54')
# C12 public/IPO year: publicly traded since 2014   vs   2016 IPO
c12=$(both '2014' '2016')

found=$((c1 + c2 + c3 + c4 + c5 + c6 + c7 + c8 + c9 + c10 + c11 + c12))

# --- 4 distractor near-misses: penalize ONLY if flagged as a CONTRADICTION ---
contra_lang='contradict|inconsist|conflict|discrepan|mismatch|does not match|do not match|cannot both|can.t both'

# D1 loyalty: 4.7M current vs 6M FY2026 target — NOT a contradiction
d1=0
if has '4\.7 ?million|4,?700,?000' && has '6 ?million|6,?000,?000'; then
  if echo "$a" | grep -qE "(loyal|member|enroll).{0,200}($contra_lang)|($contra_lang).{0,200}(loyal|member|enroll)"; then d1=1; fi
fi
# D2 Q4 forecast: $455-470M vs $420-435M — explicitly superseded
d2=0
if has '455|470' && has '420|435'; then
  if echo "$a" | grep -qE "(q4|forecast|guid).{0,200}($contra_lang)|($contra_lang).{0,200}(q4|forecast|guid)"; then d2=1; fi
fi
# D3 Home & Garden $120M subtotal vs $412M Q3 total — a subset, not a contradiction.
# Key on the distinctive "$120M / Home & Garden segment" subtotal framing, not the
# bare number 120 (which collides with "120 bps" in the margin contradiction).
d3=0
if has '\$120 ?m|120 ?million|home ?& ?garden.*\$?120|\$?120.*home ?& ?garden'; then
  if echo "$a" | grep -qE "(home ?& ?garden|segment|\\\$120|120 ?m).{0,160}($contra_lang)|($contra_lang).{0,160}(home ?& ?garden|segment|\\\$120|120 ?m)"; then d3=1; fi
fi
# D4 capex FY2025 $58M vs FY2026 $70M — different fiscal years. Key on the capex
# framing, not the bare numbers 58/70.
d4=0
if has 'capex|capital expenditure'; then
  if echo "$a" | grep -qE "(capex|capital expenditure).{0,160}($contra_lang)|($contra_lang).{0,160}(capex|capital expenditure)"; then
    if has '\$?58|58 ?m' && has '\$?70|70 ?m'; then d4=1; fi
  fi
fi

fp=$((d1 + d2 + d3 + d4))

read reward correctness < <(python3 -c "
found=$found; fp=$fp; total=12
net=max(0, found - fp)
reward=round(net/total, 4)
corr=1 if (found==total and fp==0) else 0
print(reward, corr)
")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "found": ${found}, "total_genuine": 12, "fp": ${fp}, "c1": ${c1}, "c2": ${c2}, "c3": ${c3}, "c4": ${c4}, "c5": ${c5}, "c6": ${c6}, "c7": ${c7}, "c8": ${c8}, "c9": ${c9}, "c10": ${c10}, "c11": ${c11}, "c12": ${c12}, "d1_loyalty": ${d1}, "d2_forecast": ${d2}, "d3_segment": ${d3}, "d4_capex": ${d4}}
EOF
