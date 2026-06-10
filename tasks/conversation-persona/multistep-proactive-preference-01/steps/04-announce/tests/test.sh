#!/bin/bash
# Graded (rewardkit): proactive application of 4 stated preferences to
# /app/announce.md (ISO date, 24h time, no-emoji title, D.H. sign-off),
# reward = applied/4. Shared-mode grader; rewardkit baked in the base.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
