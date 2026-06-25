#!/bin/bash
# Graded verifier (rewardkit): reward = (plan_written + correctness) / 2, carried
# by the weight-1 `score` criterion; correctness + plan_written are weight-0
# detail. rewardkit baked in the base image.
set -u
mkdir -p /logs/verifier
# Crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
