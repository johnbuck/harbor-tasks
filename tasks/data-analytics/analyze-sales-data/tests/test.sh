#!/bin/bash
# Graded verifier (rewardkit): 6 NL→analysis sub-answers, reward = correct/6,
# each gated on the input CSVs being untouched. Shared-mode grader (reads /app +
# the pristine /opt/canonical CSVs); rewardkit is baked into the base image.
# Per-criterion breakdown -> reward-details.json; reward.json stays {"reward": …}.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
