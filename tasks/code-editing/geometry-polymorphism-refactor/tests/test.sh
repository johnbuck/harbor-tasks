#!/bin/bash
# Graded completeness+quality verifier (rewardkit) for the geometry-refactor
# contract. Faithful port of the prior heredoc grader:
#
#   reward = 0.40 * visible_tests_fraction
#          + 0.40 * hidden_contract_fraction
#          + 0.20 * quality_fraction
#
# Visible pytest + hidden contract (/opt/canonical/hidden_grader.py) + quality
# gates (no test tampering / no debug cruft / no dead imports) all live in
# tests/reward.py; the weight-1 `score` criterion carries the FLAT reward.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
