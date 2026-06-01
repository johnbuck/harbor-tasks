#!/bin/bash
# UPDATE-CHURN recall scorer for PROJECT VEGA (ladder rung 2).
# 12 final-state facts, most corrected 2-3x. Precision+recall:
#   +1 per correct FINAL value
#   -1 per superseded value reported (each fact may carry up to TWO stale values)
#   -1 for the DRAFT GCP decoy
# Isolates stale-value surfacing under a saturated window: report the LAST
# correction of record, never an intermediate one.
mkdir -p /logs/verifier
a="$(tr '[:upper:]' '[:lower:]' < /app/answer.md 2>/dev/null)"
hit() { printf '%s' "$a" | grep -qE "$1"; }
s=0
# Q1 migration lead  (Reyes -> Tanaka -> Okafor)
hit "okafor" && s=$((s+1))
hit "reyes" && s=$((s-1))
hit "tanaka" && s=$((s-1))
# Q2 target date  (08-01 -> 09-15 -> 10-30)
hit "2026-10-30" && s=$((s+1))
hit "2026-08-01" && s=$((s-1))
hit "2026-09-15" && s=$((s-1))
# Q3 budget  ($2.0M -> $2.8M)
hit "2\.8" && s=$((s+1))
hit "2\.0" && s=$((s-1))
# Q4 cluster size  (48 -> 64 -> 32 nodes)
hit "\b32 node" && s=$((s+1))
hit "\b48 node" && s=$((s-1))
hit "\b64 node" && s=$((s-1))
# Q5 primary region  (us-east-1 -> us-west-2 -> eu-central-1)
hit "eu-central-1" && s=$((s+1))
hit "us-east-1" && s=$((s-1))
hit "us-west-2" && s=$((s-1))
# Q6 database engine  (PG14 -> PG16 -> Aurora)
hit "aurora" && s=$((s+1))
hit "postgresql ?14|postgres ?14|pg ?14" && s=$((s-1))
hit "postgresql ?16|postgres ?16|pg ?16" && s=$((s-1))
# Q7 cutover strategy  (big-bang -> phased -> blue-green)
hit "blue[ -]green" && s=$((s+1))
hit "big[ -]bang" && s=$((s-1))
hit "phased" && s=$((s-1))
# Q8 rollback window  (4 hours -> 90 minutes)
hit "90[ -]?min|ninety[ -]?min" && s=$((s+1))
hit "\b4 hour|four hour" && s=$((s-1))
# Q9 replication topology  (single-primary -> multi-primary)
hit "multi[ -]primary" && s=$((s+1))
hit "single[ -]primary" && s=$((s-1))
# Q10 monitoring stack  (Datadog, stable)
hit "datadog" && s=$((s+1))
# Q11 compliance tier  (SOC2, stable)
hit "soc ?2" && s=$((s+1))
# Q12 disaster-recovery site  (Dallas, stable)
hit "dallas" && s=$((s+1))
# DRAFT decoy
hit "gcp|google cloud" && s=$((s-1))
if [ "$s" -lt 0 ]; then s=0; fi
total=12
r=$(python3 -c "print(round(${s}/${total}, 4))")
if [ "$s" -eq "$total" ]; then corr=1; else corr=0; fi
echo "{\"reward\": ${r}, \"correctness\": ${corr}, \"current_facts\": ${s}}" > /logs/verifier/reward.json
