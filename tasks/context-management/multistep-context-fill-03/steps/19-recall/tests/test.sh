#!/bin/bash
# Graded (rewardkit): cross-talk LINE-ANCHORED recall over 2 projects x 6 attributes.
# reward = max(0, net slot score - distractor)/12 (weight-1 `score`; per-slot
# correctness is weight-0 detail). Shared-mode grader over /app/answer.md; rewardkit
# baked in the base. Breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
