#!/bin/bash
# Graded verifier (rewardkit): 8 cited facts about Mirador Labs, reward = matched/8.
# A fact needs the correct value + an authoritative citation in the same unit
# (wrong-value or archive-only scores 0). Shared-mode grader over /app/brief.md;
# rewardkit baked in the base. Per-criterion breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
