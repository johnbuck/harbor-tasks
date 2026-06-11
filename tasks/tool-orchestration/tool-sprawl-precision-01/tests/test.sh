#!/bin/bash
# Graded verifier (rewardkit): reward = 0.5*selection_f1 + 0.5*call_efficiency
# (carried by the weight-1 `score` criterion; F1/efficiency/precision/recall and
# call counts are weight-0 detail). The answer VALUE is not graded — only which
# tools the harness selected, read from /var/log/tool-calls.log. rewardkit is
# baked in the base. Breakdown -> reward-details.json; reward.json stays {"reward":…}.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
