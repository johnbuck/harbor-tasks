#!/bin/bash
# Graded (rewardkit): lost-in-the-middle positional recall, reward = matched/12
# (12 needle criteria → weighted_mean; per-depth rot-curve fractions + answer_present
# are weight-0 detail). Shared-mode grader over /app/answer.md; rewardkit baked in
# the base. Breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
