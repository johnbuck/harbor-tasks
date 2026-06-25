#!/bin/bash
# Graded verifier (rewardkit): precision+recall over secret-bearing files,
# reward = max(0, found - false_positives)/4 (carried by the weight-1 `score`
# criterion; per-file detection is weight-0 detail). Shared-mode grader over
# /app/findings.txt; rewardkit baked in the base. Breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
