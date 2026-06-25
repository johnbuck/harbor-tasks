#!/bin/bash
# Graded verifier (rewardkit): MUTATION coverage of the agent's slugify tests.
# reward = round(killed / 4, 4) carried by the weight-1 `reward` criterion; the two
# gates (pass_correct, impl_untouched) + the four per-mutant kills + correctness ride
# along as weight-0 detail. The grader (tests/reward/reward.py) MUTATES
# /app/stringutils.py (swaps each /tests/mutants/*.py in) and restores it. Breakdown
# -> reward-details.json. rewardkit is baked into the base image.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
