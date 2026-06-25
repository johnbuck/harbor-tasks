#!/bin/bash
# Graded verifier (rewardkit): 12 planted contradictions - 4 distractor FPs,
# reward = max(0, found - fp)/12 (carried by the weight-1 `score` criterion;
# per-contradiction + distractor-avoidance checks are weight-0 detail). Shared-mode
# grader over /app/contradictions.md; rewardkit baked in the base.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
