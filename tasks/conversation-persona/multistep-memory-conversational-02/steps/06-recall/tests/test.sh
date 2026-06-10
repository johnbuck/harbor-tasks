#!/bin/bash
# Graded recall (rewardkit): 12 of MY facts under precision pressure, reward =
# recalled/12 (each fact: MY value present AND planted sibling absent). Shared-mode
# grader over /app/answer.md; rewardkit baked in the base. Breakdown -> reward-details.json.
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
