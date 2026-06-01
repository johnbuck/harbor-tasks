#!/bin/bash
# CONTEXT-SATURATION recall scorer for PROJECT HELIOS.
# 12 current-state facts. Precision+recall with stale + decoy penalties:
#   +1 per correct CURRENT value
#   -1 per superseded (stale) value reported  -> stale-memory surfacing
#   -1 for the DRAFT decoy (2028-Q1)          -> reporting an unapproved proposal
# Two fact classes:
#   STABLE-EARLY (site B12 wk4, software wk8, integrator wk5, kickoff wk1) are
#   stated once early and never repeated -> evicted from a raw 1M window, so they
#   probe whether the harness externalises to memory.
#   UPDATE-TRAP (lead/vendor/launch/budget/sats/ops/retention/coolant) corrected
#   late -> the LATEST value is correct; the original earns a penalty.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
hit() { printf '%s' "$a" | grep -qE "$1"; }
s=0
# Q1 project lead  (Vance -> Okonkwo)
hit "okonkwo" && s=$((s+1))
hit "\bvance\b" && s=$((s-1))
# Q2 awarded antenna vendor  (... -> Brightpath -> Cardinal)
hit "cardinal" && s=$((s+1))
hit "brightpath" && s=$((s-1))
# Q3 launch window  (2027-Q3 -> 2027-Q4 ; decoy 2028-Q1)
hit "2027[ -]q4|q4[ -]2027|q4 of 2027" && s=$((s+1))
hit "2027[ -]q3|q3[ -]2027|q3 of 2027" && s=$((s-1))
hit "2028[ -]q1|q1[ -]2028|q1 of 2028" && s=$((s-1))
# Q4 budget  ($4.2M -> $5.1M)
hit "5\.1" && s=$((s+1))
hit "4\.2" && s=$((s-1))
# Q5 satellites  (6 -> 4)
hit "(4|four) satellite" && s=$((s+1))
hit "(6|six) satellite" && s=$((s-1))
# Q6 primary site  (B12, stable/evicted)
hit "b12" && s=$((s+1))
# Q7 ground software  (OrbitOS 3.1, stable/evicted)
hit "orbitos ?3\.1" && s=$((s+1))
# Q8 integration partner  (Northwind, stable/evicted)
hit "northwind" && s=$((s+1))
# Q9 data retention  (12 -> 7 years)
hit "(7|seven) year" && s=$((s+1))
hit "(12|twelve) year" && s=$((s-1))
# Q10 kickoff date  (2026-03-15, stable/evicted)
hit "2026-03-15" && s=$((s+1))
# Q11 operations center  (Denver -> Phoenix)
hit "phoenix" && s=$((s+1))
hit "denver" && s=$((s-1))
# Q12 coolant spec  (R-410A -> R-32)
hit "r-?32" && s=$((s+1))
hit "r-?410a" && s=$((s-1))
if [ "$s" -lt 0 ]; then s=0; fi
total=12
r=$(python3 -c "print(round(${s}/${total}, 4))")
if [ "$s" -eq "$total" ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"current_facts\": ${s}}" > /logs/verifier/reward.json
