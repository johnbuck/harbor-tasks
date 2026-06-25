#!/bin/bash
# ADAPTIVE-RECOVERY scorer (rewardkit port 2026-06-25). FAITHFUL conversion of the
# prior bespoke bash grader: reward = 0.6*correctness + 0.4*efficiency, byte-identical
# (full formula + the recovered / HMAC / sha256-pin / ordered-progression gates live
# in tests/reward.py). reward.py runs `dfetch --verify` (HMAC auth), the build-pinned
# sha256 authenticator check, and the progression gate; the weight-1 `score` criterion
# carries the final reward. reward.json stays a FLAT scalar dict (FOOTGUNS #2).
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
