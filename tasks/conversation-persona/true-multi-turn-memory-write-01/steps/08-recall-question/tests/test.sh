#!/bin/bash
# Graded (rewardkit): 8 recalled fields (latest-value-wins) blended with a dinner
# that respects diet+allergy: reward = (correct_fields/8)*(0.85+0.15*dinner_ok),
# carried by the weight-1 `score` criterion (fields + dinner_ok are weight-0 detail).
# Shared-mode grader over /app/answer.md; rewardkit baked in the base.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
