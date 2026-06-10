#!/bin/bash
# Graded verifier (rewardkit): 9 criteria over /app/diagnosis.md (8 content +
# 1 red-herring), reward = satisfied/9. Shared-mode grader; rewardkit baked in
# the base image. Per-criterion breakdown -> reward-details.json; reward.json
# stays {"reward": <float>} (Hard Rule #2).
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
