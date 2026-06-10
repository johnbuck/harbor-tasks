#!/bin/bash
# Graded verifier (rewardkit): 10 cited-fact items, reward = found/10. Each item
# needs the current value + an authoritative citation (archive-only or wrong-value
# scores 0). Shared-mode grader over /app/answer.md; rewardkit baked in the base.
# Per-criterion breakdown -> reward-details.json; reward.json stays {"reward": …}.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
