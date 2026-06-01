#!/bin/bash
# Ingest step: not scored (multi_step_reward_strategy="final"; only the recall
# step's reward counts). Emit a neutral scalar so the step completes.
mkdir -p /logs/verifier
echo '{"reward": 1.0}' > /logs/verifier/reward.json
