#!/bin/bash
# Graded verifier (rewardkit): precision+recall over secret-bearing files,
# reward = max(0, found - false_positives)/4 (carried by the weight-1 `score`
# criterion; per-file detection is weight-0 detail). Shared-mode grader over
# /app/findings.txt; rewardkit baked in the base. Breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
