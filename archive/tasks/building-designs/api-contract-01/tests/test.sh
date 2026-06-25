#!/bin/bash
# Graded verifier (rewardkit): 16 OpenAPI structural criteria, reward = passed/16.
# Runs in the SEPARATE verifier sandbox; grades only the declared artifact
# (/app/openapi.yaml). rewardkit is baked into the verifier image (tests/Dockerfile)
# so this needs no network. Per-criterion breakdown -> reward-details.json;
# reward.json stays {"reward": <float>} (Hard Rule #2).
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
