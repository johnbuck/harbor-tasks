#!/bin/bash
# Graded verifier (rewardkit): 5 KEY=value log-analysis sub-results, reward =
# correct/5, each gated on the input access.log being untouched. Shared-mode
# grader (reads /app + the pristine /opt/canonical/access.log); rewardkit is
# installed in the task image. Per-criterion breakdown -> reward-details.json;
# reward.json stays {"reward": <float>} (Hard Rule #2).
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
