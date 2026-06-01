#!/bin/bash
# CROSS-TALK PRECISION recall scorer for PROJECTS ORION & LYRA (ladder rung 3).
# 12 slots = 6 attributes x 2 projects. Line-anchored per (project, attribute):
#   +1 if the correct value appears on that slot's line
#   -1 if the SIBLING project's value appears there (cross-attribution)
# Tests attribution under heavy interleaving across a saturated window.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
# line(project, attr_regex) -> the agent's line(s) for that slot
line() { printf '%s\n' "$a" | grep -E "$1" | grep -E "$2"; }
on() { printf '%s' "$1" | grep -qE "$2"; }
s=0

score() {  # $1=slot line  $2=correct regex  $3=sibling regex
  on "$1" "$2" && s=$((s+1))
  on "$1" "$3" && s=$((s-1))
}

# Leadership: Orion=Marsh, Lyra=Crane
score "$(line 'orion' 'lead')"      "marsh"          "crane"
score "$(line 'lyra' 'lead')"       "crane"          "marsh"
# Budget: Orion=$7.4M, Lyra=$3.6M
score "$(line 'orion' 'budget')"    "7\.4"           "3\.6"
score "$(line 'lyra' 'budget')"     "3\.6"           "7\.4"
# Site: Orion=K9, Lyra=Frankfurt
score "$(line 'orion' 'site')"      "k9"             "frankfurt"
score "$(line 'lyra' 'site')"       "frankfurt"      "k9"
# Vendor: Orion=Heliosat, Lyra=Brightlink
score "$(line 'orion' 'vendor|partner')"  "heliosat"  "brightlink"
score "$(line 'lyra' 'vendor|partner')"   "brightlink" "heliosat"
# Headcount: Orion=38, Lyra=52
score "$(line 'orion' 'headcount|engineer')"  "\b38"   "\b52"
score "$(line 'lyra' 'headcount|engineer')"   "\b52"   "\b38"
# Go-live: Orion=2027-Q2, Lyra=2026-Q4
score "$(line 'orion' 'go-live|schedule|launch')"  "2027[ -]?q2|q2[ -]?2027"  "2026[ -]?q4|q4[ -]?2026"
score "$(line 'lyra' 'go-live|schedule|launch')"   "2026[ -]?q4|q4[ -]?2026"  "2027[ -]?q2|q2[ -]?2027"

# DRAFT decoy: Project Nova must not appear
on "$a" "nova|reykjavik|9\.9" && s=$((s-1))

if [ "$s" -lt 0 ]; then s=0; fi
total=12
r=$(python3 -c "print(round(${s}/${total}, 4))")
if [ "$s" -eq "$total" ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"current_facts\": ${s}}" > /logs/verifier/reward.json
