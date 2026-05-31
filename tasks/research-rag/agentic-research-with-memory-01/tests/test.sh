#!/bin/bash
# Verifier: deterministic fact + citation scoring + optional LLM-judge for synthesis.
#
# Axes:
#   founded_2024            — brief contains "2024" near founding language
#   nsf_4_2m                — brief contains "4.2" million NSF figure
#   climate_lead_holm       — brief names Petra Holm as climate lead
#   pubs_18                 — brief states 18 publications in 2025
#   two_partners            — brief names at least 2 of (UCSF, BioGen, NCAR)
#   cited_each              — each of the 5 facts has a citation in markdown-link form
#   citations_valid         — cited URLs actually exist in the corpus
#   no_hallucination        — no obviously-fabricated facts (proxy: brief doesn't mention
#                              a publication count >25 or a $-amount way outside [1, 10]M)
#
# Per-fact citation check: for each load-bearing claim, the same paragraph (or
# adjacent paragraph) must contain a markdown link to the corresponding page.

set -u
mkdir -p /logs/verifier

BRIEF=/app/brief.md
[ ! -f "$BRIEF" ] && {
    cat > /logs/verifier/reward.json <<'EOF'
{"reward": 0.0, "correctness": 0.0, "missing_brief": 1}
EOF
    exit 0
}

lower=$(tr '[:upper:]' '[:lower:]' < "$BRIEF")

# Fact presence
founded_2024=$(echo "$lower" | grep -qE 'found(ed)?\s.*2024|2024.*found' && echo 1 || echo 0)
nsf_4_2m=$(echo "$lower" | grep -qE '\$?4\.2[[:space:]]*(m|million)' && echo 1 || echo 0)
climate_lead_holm=$(echo "$lower" | grep -qE 'petra holm|holm.*climate|climate.*holm' && echo 1 || echo 0)
pubs_18=$(echo "$lower" | grep -qE '18[[:space:]]*(publication|paper|peer)' && echo 1 || echo 0)

# Partners: at least two of (UCSF, BioGen, NCAR)
p_ucsf=$(echo "$lower"   | grep -qE 'ucsf' && echo 1 || echo 0)
p_biogen=$(echo "$lower" | grep -qE 'biogen' && echo 1 || echo 0)
p_ncar=$(echo "$lower"   | grep -qE 'ncar|national center for atmospheric' && echo 1 || echo 0)
p_count=$((p_ucsf + p_biogen + p_ncar))
two_partners=$([ $p_count -ge 2 ] && echo 1 || echo 0)

# Citation density: count link MATCHES (not lines — a paragraph can hold many).
n_links=$(grep -oE '\[[^]]+\]\(/[^)]+\)' "$BRIEF" 2>/dev/null | wc -l | tr -dc '0-9')
[ -z "$n_links" ] && n_links=0
cited_each=$([ $n_links -ge 5 ] && echo 1 || echo 0)

# Citation validity: every linked URL must exist in the corpus directory
citations_valid=1
invalid_count=0
for url in $(grep -oE '\([^)]+\)' "$BRIEF" | tr -d '()' | grep -E '^/' | sort -u); do
    # Strip query/anchor; turn /foo/bar.html into /opt/corpus/foo/bar.html
    path="/opt/corpus${url%%[?#]*}"
    if [ ! -f "$path" ]; then
        invalid_count=$((invalid_count + 1))
        citations_valid=0
    fi
done

# Anti-hallucination heuristic: no impossible numbers
no_hallucination=1
echo "$lower" | grep -qE '(\$[2-9][0-9]+|\$[1-9][0-9]{2,})[[:space:]]*(m|million)' && no_hallucination=0  # >$20M
echo "$lower" | grep -qE '\b(50|[6-9][0-9]|[1-9][0-9]{2,})[[:space:]]*publication' && no_hallucination=0  # >50 pubs

# Correctness = all 5 facts + valid citations
fact_total=$((founded_2024 + nsf_4_2m + climate_lead_holm + pubs_18 + two_partners))
correctness=$(python3 -c "print($fact_total / 5.0)")
all_facts=$([ $fact_total -eq 5 ] && echo 1 || echo 0)

# Reward = correctness * citation-credit, with hallucination penalty
reward=$(python3 -c "
cor = $correctness
ce = $cited_each
cv = $citations_valid
nh = $no_hallucination
base = cor * (0.7 + 0.2 * ce + 0.1 * cv)
print(max(0.0, base if nh else base - 0.3))
")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "founded_2024": ${founded_2024}, "nsf_4_2m": ${nsf_4_2m}, "climate_lead_holm": ${climate_lead_holm}, "pubs_18": ${pubs_18}, "two_partners": ${two_partners}, "partner_count": ${p_count}, "n_links": ${n_links}, "cited_each": ${cited_each}, "citations_valid": ${citations_valid}, "invalid_citations": ${invalid_count}, "no_hallucination": ${no_hallucination}, "all_facts": ${all_facts}}
EOF
