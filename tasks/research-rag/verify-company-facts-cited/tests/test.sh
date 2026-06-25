#!/bin/bash
# Graded verifier (rewardkit): 10 cited-fact items, reward = found/10. Each item
# needs the current value + an authoritative citation (archive-only or wrong-value
# scores 0). Shared-mode grader over /app/answer.md; rewardkit baked in the base.
# Per-criterion breakdown -> reward-details.json; reward.json stays {"reward": …}.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
