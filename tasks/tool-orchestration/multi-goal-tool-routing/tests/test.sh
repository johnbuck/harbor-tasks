#!/bin/bash
# Graded verifier (rewardkit): reward = 0.5*answer_fraction + 0.5*tool_f1 (carried
# by the weight-1 `score` criterion; the 3 answer checks + F1 are weight-0 detail).
# Shared-mode grader over /app/answer.json + /var/log/tool-calls.log; rewardkit
# baked in the base. Breakdown -> reward-details.json; reward.json stays {"reward":…}.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
