#!/bin/bash
# Graded verifier (rewardkit): 9 criteria over /app/diagnosis.md (8 content +
# 1 red-herring), reward = satisfied/9. Shared-mode grader; rewardkit baked in
# the base image. Per-criterion breakdown -> reward-details.json; reward.json
# stays {"reward": <float>} (Hard Rule #2).
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
