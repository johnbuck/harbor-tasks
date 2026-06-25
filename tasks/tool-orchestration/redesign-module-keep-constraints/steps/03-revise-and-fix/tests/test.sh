#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
# Scoring is ported to rewardkit (tests/reward.py): reward = clamp(0.40) +
# functional(0.40) + cleanup(0.12) + replan(0.08), carried by the weight-1
# `score` criterion; the four dimensions + correctness are weight-0 detail.
set -u
mkdir -p /logs/verifier

# Independent scratch-wipe assertion (workdir/setup.sh sources the canonical wipe;
# multi_step treats its failure as only a warning). The clamp bound is a memory
# discriminator, so a stashed note in scratch would void the result — fail loudly
# (flat reward 0.0) if one survived. This guard precedes the rewardkit scoring.
if find /tmp /var/tmp /logs/agent -maxdepth 3 -name 'clamp_note*' 2>/dev/null | grep -q .; then
    echo '{"reward": 0.0}' > /logs/verifier/reward.json
    echo "WIPE ASSERTION FAILED: scratch survived the pre-revise wipe" >&2
    exit 1
fi

# Crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
