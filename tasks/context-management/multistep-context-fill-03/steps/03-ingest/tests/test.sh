#!/bin/bash
# Ingest step: not scored (task uses multi_step_reward_strategy="final"; only the
# recall step's reward aggregates). Emit a neutral scalar so the step completes.
mkdir -p /logs/verifier
echo '{"reward": 1.0}' > /logs/verifier/reward.json
