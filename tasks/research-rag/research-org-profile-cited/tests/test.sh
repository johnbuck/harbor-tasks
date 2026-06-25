#!/bin/bash
# Graded verifier (rewardkit): 8 cited facts about Mirador Labs, reward = matched/8.
# A fact needs the correct value + an authoritative citation in the same unit
# (wrong-value or archive-only scores 0). Shared-mode grader over /app/brief.md;
# rewardkit baked in the base. Per-criterion breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
