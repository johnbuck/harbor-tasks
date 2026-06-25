#!/bin/bash
# Graded (rewardkit): proactive application of 4 stated preferences to
# /app/announce.md (ISO date, 24h time, no-emoji title, D.H. sign-off),
# reward = applied/4. Shared-mode grader; rewardkit baked in the base.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
