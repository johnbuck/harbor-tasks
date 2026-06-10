#!/bin/bash
# Graded verifier (rewardkit): 6 NL→analysis sub-answers, reward = correct/6,
# each gated on the input CSVs being untouched. Shared-mode grader (reads /app +
# the pristine /opt/canonical CSVs); rewardkit is baked into the base image.
# Per-criterion breakdown -> reward-details.json; reward.json stays {"reward": …}.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
