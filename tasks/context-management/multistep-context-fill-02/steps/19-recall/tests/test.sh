#!/bin/bash
# Graded (rewardkit): long-context UPDATE-trap recall. reward =
# max(0, current_hits - stale_hits)/12 (weight-1 `score`; per-fact recall + no-stale
# are weight-0 detail). Shared-mode grader over /app/answer.md; rewardkit baked in
# the base. Breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
