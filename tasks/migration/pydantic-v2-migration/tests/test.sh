#!/bin/bash
# Graded verifier (rewardkit) for pydantic-v2-migration — faithful port of the
# prior per-migration-site pytest grader. reward = round(satisfied/9, 4) over the
# 9 pinned behavioral tests in /app/tests/test_settings.py (carried by the
# weight-1 `score` criterion; per-site pass/fail, the tamper check, and
# answer_present are weight-0 detail in reward-details.json). A tampered test
# file (differs from the pristine /opt/canonical copy) -> reward 0.
set -u
mkdir -p /logs/verifier
# S4 crash guard: a rewardkit exception that writes no reward.json makes Harbor
# silently DROP the trial (FOOTGUNS #2). Guarantee a flat numeric reward.json.
rewardkit /tests --workspace /app --output /logs/verifier/reward.json \
    || echo '{"reward": 0.0}' > /logs/verifier/reward.json
