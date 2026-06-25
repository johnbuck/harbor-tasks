#!/bin/bash
# Graded verifier (rewardkit). 8 files x 2 sub-checks = 16; reward = passed/16.
#
# Runs in the SEPARATE verifier sandbox (task.toml environment_mode = "separate").
# Expected is RECOMPUTED from /app/data at grade time (tests/reward.py) — no answer
# key anywhere (the deprecated /app/expected/ leak is gone). Per-criterion results
# go to /logs/verifier/reward-details.json (shown in `harbor view`); reward.json
# stays {"reward": <float>} (FOOTGUNS #38).
#
# rewardkit is BAKED into the verifier image (tests/Dockerfile: pip install
# harbor-rewardkit==0.1.4), so grading has NO runtime network dependency — call the
# baked `rewardkit` directly (it uses the image python; reward.py is stdlib +
# rewardkit only, so FOOTGUNS #7's uvx-python-shadow concern doesn't apply).
set -u
mkdir -p /logs/verifier
# S4 crash guard (FOOTGUNS #2): if rewardkit throws and writes nothing, Harbor
# silently DROPS the trial. Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
