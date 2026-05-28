#!/bin/bash
# Verifier: run the LLM judge.
mkdir -p /logs/verifier
python3 "$(dirname "$0")/llm_judge.py" 2>&1 || true

# llm_judge.py writes reward.json itself; ensure it exists as fallback
if [ ! -f /logs/verifier/reward.json ]; then
    echo '{"reward": 0.0}' > /logs/verifier/reward.json
fi
