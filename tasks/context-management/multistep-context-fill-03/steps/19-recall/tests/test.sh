#!/bin/bash
# Graded recall (rewardkit) over /app/answer.md; rewardkit baked in the base.
# Per-fact breakdown -> reward-details.json; reward.json stays {"reward": ...}.
set -u
mkdir -p /logs/verifier

# Independent wipe assertion: multi_step.py treats a setup.sh failure as ONLY a
# warning, so the graded step re-checks that the pre-recall scratch wipe took. If
# a wiped ground-truth/scratch surface survived, fail loudly (flat reward 0.0)
# rather than grade an answer that could be a re-read.
if [ -d /app/reports ] || find /tmp /var/tmp -maxdepth 3 -name 'recall_notes*' 2>/dev/null | grep -q .; then
    echo '{"reward": 0.0}' > /logs/verifier/reward.json
    echo "WIPE ASSERTION FAILED: scratch survived the pre-recall wipe" >&2
    exit 1
fi

# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
