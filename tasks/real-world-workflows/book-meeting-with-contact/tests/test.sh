#!/bin/bash
# Graded verifier (rewardkit) for schedule-meeting-from-name.
# reward = fraction of N=17 independent sub-checks passed. The task threads state
# across several steps (resolve referent -> compute earliest valid slot -> email
# -> parse a COUNTER-PROPOSAL reply -> book the AGREED slot -> confirm ->
# summarize). Each of those is its own +1, so a harness that loses track of the
# counter-proposal, mis-computes the earliest slot, double-books, or clutters the
# outbox scores a partial fraction instead of a saturated 0/1. Faithful port of
# the prior bash grader; the exact aggregate lives in the weight-1 `score`
# criterion (reward.py), per-check detail rides weight-0.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
