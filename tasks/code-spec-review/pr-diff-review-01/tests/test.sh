#!/bin/bash
# Graded verifier (rewardkit): precision+recall over the planted issue set,
# reward = max(0, found - red-herring FP)/3 (carried by the weight-1 `score`
# criterion; per-issue checks are weight-0 detail). Shared-mode grader over
# /app/review.md; rewardkit baked in the base. Breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
