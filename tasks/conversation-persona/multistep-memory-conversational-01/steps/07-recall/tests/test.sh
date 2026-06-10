#!/bin/bash
# Graded recall (rewardkit): 12 of MY facts under precision pressure, reward =
# recalled/12. Each fact needs MY value(s) present AND the planted sibling absent
# (sibling penalty). Shared-mode grader over /app/answer.md; rewardkit baked in
# the base. Per-fact breakdown -> reward-details.json; reward.json stays {"reward":…}.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
