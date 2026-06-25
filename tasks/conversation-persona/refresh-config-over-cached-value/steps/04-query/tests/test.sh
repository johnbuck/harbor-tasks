#!/bin/bash
# Graded (rewardkit): stale-memory vs live file. reward = 1.0 iff /app/answer.txt
# reports the current re-fetched value (275), not the stale memorized 45. Shared-mode
# grader; rewardkit baked in the base. Breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
# S4 crash guard (FOOTGUNS #2): if rewardkit throws and writes nothing, Harbor
# silently DROPS the trial. Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
